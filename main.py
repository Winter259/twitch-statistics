import requests
from time import sleep, strftime
from pysqlite import Pysqlite
from pprint import pprint

create_statement = 'CREATE TABLE IF NOT EXISTS `{}` (`id` ' \
                   'INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,' \
                   '`viewers`	INTEGER NOT NULL,' \
                   '`followers`	INTEGER NOT NULL,' \
                   '`partner`	INTEGER NOT NULL,' \
                   '`time` TEXT NOT NULL)'


def pause(amount=5):
    for time in range(amount, 0, -1):
        print('[+] Paused for {} seconds   '.format(time), end='\r')
        sleep(1)
    print('                                    ', end='\r')


def create_streamer_table(db, streamer):
    try:
        db.execute_sql('{}'.format(create_statement.format(streamer)))
        # TODO: add some sort of feedback for if the table already exists
    except Exception as e:
        print(e)


def insert_data_into_db(db, streamer, viewers, followers, partner):
    try:
        db.insert_db_data(streamer, '(NULL, ?, ?, ?, CURRENT_TIMESTAMP)', (viewers, followers, partner))
        print('[+] Statistics successfully written to the database')
    except Exception as e:
        print(e)


def main():
    cycle_delay = 10  # seconds
    streamer_delay = 2  # seconds
    database = Pysqlite('twitch_stats', 'twitch_stats_v2.db')
    while True:
        json_url_streams = 'https://api.twitch.tv/kraken/search/streams?q=Elite%20Dangerous'
        # initial api ping to get the first set of streamers
        try:
            data_games = requests.get(json_url_streams).json()
        except Exception as e:
            print('[-] Error getting JSON data for streamer list: {}'.format(e))
            sleep(10)  # delay before trying again
        else:
            # pprint(data_games)
            stream_count = data_games['_total']
            print('[+] Streams online: {}'.format(stream_count))
            print('[+] Determining streamer count')
            current_count = 0
            while current_count < int(stream_count):
                print('[+] Streamers: {}/{}'.format(current_count, stream_count))
                # only ping the api again if you are not on the first page
                if not current_count == 0:
                    next_json_url = data_games['_links']['next']
                    print('[+] Accessing url: {}'.format(next_json_url))
                    try:
                        data_games = requests.get(next_json_url).json()
                    except Exception as e:
                        print('[-] Error getting JSON data for streamer list: {}'.format(e))
                streamers_data = data_games['streams']
                for streamer_data in streamers_data:
                    streamer_name = streamer_data['channel']['name']
                    # create a table for each streamer. The method avoids duplicates itself
                    if streamer_data['game'] == 'Elite: Dangerous':
                        create_streamer_table(database, streamer_name)
                        # get the data for this streamer
                        viewer_count = streamer_data['viewers']
                        follower_count = streamer_data['channel']['followers']
                        partnership = 0
                        if streamer_data['channel']['partner']:
                            partnership = 1
                        print('[+] Info for: {}\n\tGame: {}\n\tViewers: {}\n\tFollowers: {}\n\tPartner: {}'.format(
                            streamer_name,
                            streamer_data['game'],
                            viewer_count,
                            follower_count,
                            partnership == 1
                        ))
                        # api search isn't perfect despite filtering for E:D only
                        insert_data_into_db(database, streamer_name, viewer_count, follower_count, partnership)
                    else:
                        print('[-] {} is currently not playing Elite: Dangerous'.format(streamer_name))
                    pause(streamer_delay)
                current_count += 10
        pause(cycle_delay)

if __name__ == '__main__':
    main()
