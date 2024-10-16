from views.tournament_view import View
from models.tournament import Tournament
from utils.report_util import ReportUtil
import json
import glob
import os



class TournamentController:
    def __init__(self):
        # Initialize the tournament attribute
        self.tournament = None
    
    def load (self, name):
        # Load tournament data from a JSON file based on the tournament name.
        self.tournament = Tournament(name, None, None, None, None)
        is_data_loaded = self.tournament.load()
        if not is_data_loaded:
            self.tournament = None
            return False
        return True

    def create_tournament(self, details = None):
        # Create a new tournament using user-provided details.
        tmt_name, tmt_location, tmt_start_date, tmt_end_date, tmt_description = (
            View.create_tournament_view(details)
        )
        # Check if the user wants to exit the creation process with pressing 0
        if tmt_name == '0' or tmt_location == '0' or tmt_start_date == '0' or tmt_end_date == '0' or tmt_description == '0':
            data = {"option_number":1,
                    "tmt_name":tmt_name,
                    "tmt_location":tmt_location,
                    "tmt_start_date": tmt_start_date,
                    "tmt_end_date": tmt_end_date,
                    "tmt_description": tmt_description
                    }
            
            # Save the current state to resume later from P4\utils\report_util.py
            ReportUtil.save_resume_file(data)
            return False
        else:
            # Create and save the tournament
            self.tournament = Tournament(
                tmt_name, tmt_location, tmt_start_date, tmt_end_date, tmt_description
            )
            self.tournament.save()
            return True
        
    # Register a player to the tournament.
    def register_player(self, details= None, option_number = None):
        details = View.register_player(details)
        if "0" in details.values():
            details["option_number"] = option_number
            details["tournament"] = self.tournament.name
            # Save the current state to resume later from P4\utils\report_util.py
            self.save_backup(details)
            return False
        else:
            if details["chess_id"] in self.tournament.get_reg_player_ids():
                print("Player is already registered")
            else:
                self.tournament.register_player(
                    chess_id, last_name, first_name, birthday, country, club_name)
            return True
        
    def save_backup(data):
        # Assurer que le répertoire existe
        os.makedirs("resources", exist_ok=True)
        with open("resources/resume_file.json", "w") as file:
            json.dump(data, file, indent=4) 
    # Start the tournament and handle the rounds and matches.
    def start_tournament(self, details = None):
        self.tournament.reset_rounds()
        self.tournament.set_total_nbr_rounds()
        # Iterate through each round
        for round in range(self.tournament.number_of_rounds):
            self.tournament.generate_round()
            for match in self.tournament.rounds[round].rnd_matches:
                while True:
                    # Prompt the user for the match result
                    ask_result = View.ask_match_result(match.player1,match.player2)
                    if ask_result == 1 or ask_result == 2 :
                        break
                    elif ask_result != 3:
                        print("please enter a valid option:")
                    elif ask_result == 3:
                        print("match is draw, the players are playing again.")
                        
                # Update the match based on the result        
                match.play(ask_result)
                print(match.player1.first_name,match.player1.plyr_score, "//" ,match.player2.first_name,match.player2.plyr_score)
            number_of_winners, winners = self.tournament.start_round()
            self.tournament.add_rounds_to_file()
            if number_of_winners == 1:
                print("final winner decided") 
                print("the tournament winner is", winners[0].first_name)
                break
            print("no final winner yet")
        return True

    def see_all_players(self,details = None):
        # Display all players from the clubs.json file.
        with open("resources/clubs.json", "r") as file:
            data = json.load(file)
            all_players = {}
            player_details = {}
            longest_first_name = longest_last_name = longest_fed_name = longest_club_name = 0
            # Iterate through federations, clubs, and players to collect data
            for federation in data["federations"]:
                for club in federation["clubs"]:
                    for player in club["players"]:
                        key = f"{player['last_name']} {player['first_name']}"
                        value = f"{player['national_chess_id']}"
                        all_players[key] = value
                        player_details[key] = [
                            player['national_chess_id'],
                            player['last_name'],
                            player['first_name'],
                            federation["name"],
                            club["club_name"]
                        ]
                        # Update the maximum lengths for formatting
                        longest_first_name = max(longest_first_name,len(player["first_name"]))
                        longest_last_name = max(longest_last_name,len(player["last_name"]))
                        longest_fed_name = max(longest_fed_name,len(federation["name"]))
                        longest_club_name = max(longest_club_name,len(club["club_name"]))
            all_players = dict(sorted(all_players.items()))
            # Display the players
            report_ask = View.show_all_players(all_players)
            if report_ask.lower() == "y":
                # Generate a report
                report = []
                report.append(f'| Chess Id | {"LN":<{longest_last_name}} | {"FN":<{longest_first_name}} | {"FED":<{longest_fed_name}} | {"CLUB":<{longest_club_name}} | \n')
                report.append(f'| ________ | {"_"*(longest_last_name)} | {"_"*(longest_first_name)} | {"_"*(longest_fed_name)} | {"_"*(longest_club_name)} | \n')
                for name in all_players:
                    player = player_details[name]
                    report.append(f'| {player[0]:<8} | {player[1]:<{longest_last_name}} | {player[2]:<{longest_first_name}} | {player[3]:<{longest_fed_name}} | {player[4]:<{longest_club_name}} |\n')
                    # Write the report to a file
                with open("resources/reports/all_players_report.txt","w") as file:
                    file.writelines(report) 
                    print("report has been generated")
        return True
                
    # Display all tournaments and optionally generate a report.
    def see_all_tournaments(self, details = None):
        path = os.path.join("resources/tournaments", "*.json")
        file_names = glob.glob(path)
        # print(file_names)
        tournaments = []
        for file_name in file_names:
            with open(file_name) as file:
                data = json.load(file)
                tournaments.append(data)
        longest_t_name = longest_location = 0
        for tournament in tournaments:
            View.show_all_tournaments(tournament)
            # Update the maximum lengths for formatting
            longest_t_name =max(longest_t_name,len(tournament["name"]))
            longest_location =max(longest_location,len(tournament["location"])) 
        ask_report = View.ask_for_report()
        if ask_report == "y":
            # Generate a report
            report = []
            report.append(f'| {"TName":<{longest_t_name}} | {"Location":<{max(longest_location,8)}} | {"Start date":<10} | {"End date":<10} | \n')
            report.append(f'| {"_"*(longest_t_name)} | {"_"*(max(longest_location,8))} | {"_"*10} | {"_"*10} | \n')
            for tournament in tournaments:
                report.append(f'| {tournament["name"]:<{longest_t_name}} | {tournament["location"]:<{max(longest_location,8)}} | {tournament["start_date"]:<10} | {tournament["end_date"]:<10} |\n')
                # Write the report to a file
            with open("resources/reports/all_tournaments_report.txt","w") as file:
                file.writelines(report) 
                print("tournaments report has been generated")
        return True
            
    # Search for a particular tournament and display its details.
    def search_tournament(self,details = None):
        print(self.tournament)
        ask_report = View.ask_for_report()
        if ask_report == "y":
            # Generate a report
            report = []
            report.append(f'| {"TName":<{len(self.tournament.name)}} | {"Start date":<10} | {"End date":<10} | \n')
            report.append(f'| {"_"*len(self.tournament.name)} | {"_"*10} | {"_"*10} | \n')
            report.append(f'| {self.tournament.name:<{len(self.tournament.name)}} | {self.tournament.start_date:<10} | {self.tournament.end_date:<10} | \n')
            # Write the report to a file
            with open(f"resources/reports/{self.tournament.name}_report.txt","w") as file:
                file.writelines(report) 
                print(f"{self.tournament.name}'s report has been generated")
        return True
    
    # Display all players registered in a particular tournament.
    def show_tournament_players(self,details = None):
        players = self.tournament.registered_players
        all_players = {}
        player_details = {}
        longest_first_name = longest_last_name = 0
        # print(players)
        for player in players:
            key = f"{player.last_name} {player.first_name}"
            value = f"{player.national_chess_id}"
            all_players[key] = value
            player_details[key] = [
                player.national_chess_id,
                player.last_name,
                player.first_name,
                player.date_of_birth
                ]
            # Update the maximum lengths for formatting
            longest_first_name = max(longest_first_name,len(player.first_name))
            longest_last_name = max(longest_last_name,len(player.last_name))
        all_players = dict(sorted(all_players.items()))
        # Display the players
        report_ask = View.show_all_players(all_players)
        if report_ask.lower() == "y":
            # Generate a report
            report = []
            report.append(f'| Chess Id | {"LN":<{longest_last_name}} | {"FN":{longest_first_name}} | {"DOB":<{10}} | \n')
            report.append(f'| ________ | {"_"*(longest_last_name)} | {"_"*(longest_first_name)} | {"_"*(10)} | \n')
            for name in all_players:
                player = player_details[name]
                report.append(f'| {player[0]:<8} | {player[1]:{longest_last_name}} | {player[2]:<{longest_first_name}} | {player[3]:<{10}} |\n')
            # Write the report to a file
            with open(f"resources/reports/reg_players_{self.tournament.name}_report.txt","w") as file:
                file.writelines(report) 
                print(f"{self.tournament.name}'s players report has been generated")
        return True
        
    # Display all rounds and matches in the tournament.
    def show_tournament_report(self, details = None):
        longest_first_name = longest_last_name = 0
        for round in self.tournament.rounds:
            View.show_tournament_round(
                round.rnd_name, round.rnd_start_datetime, round.rnd_end_datetime
            )
            for match in round.rnd_matches:
                View.show_round_matches(match.player1, match.player2)
                # Update the maximum lengths for formatting
                longest_first_name = max(longest_first_name,len(match.player1.first_name),len(match.player2.last_name))
                longest_last_name = max(longest_last_name,len(match.player1.last_name),len(match.player2.last_name))
                
        ask_report = View.ask_for_report()
        if ask_report.lower() == "y":
            # Generate a report
            report = []
            report.append(f'| Round n | {"Round SD":<{20}} | {"Round ED":<{20}} | P1 Chess Id | {"P1 LN":<{longest_last_name}} | {"P1 FN":{longest_first_name}} | {"P1 Score":<{7}} | P2 Chess Id | {"P2 LN":<{longest_last_name}} | {"P2 FN":{longest_first_name}} | {"P2 Score":<{8}} | \n')
            report.append(f'| {"_"*(7)} | {"_"*(20)} | {"_"*(20)} | {"_"*(11)} | {"_"*(longest_last_name)} | {"_"*(longest_first_name)} | {"_"*(8)} | {"_"*(11)} | {"_"*(longest_last_name)} | {"_"*(longest_first_name)} | {"_"*(8)} | \n')
            for round in self.tournament.rounds :
                for match in round.rnd_matches :
                    report.append(f'| {round.rnd_name:<{7}} | {round.rnd_start_datetime:<{20}} | {round.rnd_end_datetime:<{20}} | {match.player1.national_chess_id:<{11}} | {match.player1.last_name:<{longest_last_name}} | {match.player1.first_name:{longest_first_name}} | {match.player1.plyr_score:<{8}} | {match.player2.national_chess_id :<{11}} | {match.player2.last_name:<{longest_last_name}} | {match.player2.first_name:{longest_first_name}} | {match.player2.plyr_score:<{8}} | \n')
            # Write the report to a file
            with open(f"resources/reports/rounds_&_matches_{self.tournament.name}_report.txt","w") as file:
                file.writelines(report) 
                print(f"{self.tournament.name}'s rounds and matches report has been generated")
        return True