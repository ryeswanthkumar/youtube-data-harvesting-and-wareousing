from googleapiclient.discovery import build
import mysql.connector
import pandas as pd
import streamlit as st
import MySQLdb
import datetime
from streamlit_option_menu import option_menu




#API key connection

def Api_connect():
    Api_Id="AIzaSyD_QH0udRH86RiL-6zSKY0sLW50sK39TKs"

    api_service_name="youtube"
    api_version="v3"

    youtube=build(api_service_name,api_version,developerKey=Api_Id)

    return youtube

youtube=Api_connect()




#get channels information

def get_channel_info(channel_id):
    request=youtube.channels().list(
                part="snippet,ContentDetails,statistics",
                id=channel_id
    )
    response=request.execute()

    for i in response['items']:
        data=dict(Channel_Name=i["snippet"]["title"],
                Channel_Id=i["id"],
                Subscribers=i['statistics']['subscriberCount'],
                Views=i["statistics"]["viewCount"],
                Total_Videos=i["statistics"]["videoCount"],
                Channel_Description=i["snippet"]["description"],
                Playlist_Id=i["contentDetails"]["relatedPlaylists"]["uploads"])
    return data





#get video ids
def get_videos_ids(channel_id):
    video_ids=[]
    response=youtube.channels().list(id=channel_id,
                                    part='contentDetails').execute()
    Playlist_Id=response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    next_page_token=None

    while True:
        response1=youtube.playlistItems().list(
                                            part='snippet',
                                            playlistId=Playlist_Id,
                                            maxResults=50,
                                            pageToken=next_page_token).execute()
        for i in range(len(response1['items'])):
            video_ids.append(response1['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token=response1.get('nextPageToken')

        if next_page_token is None:
            break
    return video_ids



#get video information
def get_video_info(video_ids):
    video_data=[]
    for video_id in video_ids:
        request=youtube.videos().list(
            part="snippet,ContentDetails,statistics",
            id=video_id
        )
        response=request.execute()

        for item in response["items"]:
            data=dict(Channel_Name=item['snippet']['channelTitle'],
                    Channel_Id=item['snippet']['channelId'],
                    Video_Id=item['id'],
                    Title=item['snippet']['title'],
                    Tags=item['snippet'].get('tags'),
                    Thumbnail=item['snippet']['thumbnails']['default']['url'],
                    Description=item['snippet'].get('description'),
                    Published_Date=item['snippet']['publishedAt'],
                    Duration=item['contentDetails']['duration'],
                    Views=item['statistics'].get('viewCount'),
                    Likes=item['statistics'].get('likeCount'),
                    Comments=item['statistics'].get('commentCount'),
                    Favorite_Count=item['statistics']['favoriteCount'],
                    Definition=item['contentDetails']['definition'],
                    Caption_Status=item['contentDetails']['caption']
                    )
            video_data.append(data)    
    return video_data




#get comment information
def get_comment_info(video_ids):
    Comment_data=[]
    try:
        for video_id in video_ids:
            request=youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=50
            )
            response=request.execute()

            for item in response['items']:
                data=dict(Comment_Id=item['snippet']['topLevelComment']['id'],
                        Video_Id=item['snippet']['topLevelComment']['snippet']['videoId'],
                        Comment_Text=item['snippet']['topLevelComment']['snippet']['textDisplay'],
                        Comment_Author=item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                        Comment_Published=item['snippet']['topLevelComment']['snippet']['publishedAt'])
                
                Comment_data.append(data)
                
    except:
        pass
    return Comment_data





#get_playlist_details

def get_playlist_details(channel_id):
        next_page_token=None
        All_data=[]
        while True:
                request=youtube.playlists().list(
                        part='snippet,contentDetails',
                        channelId=channel_id,
                        maxResults=50,
                        pageToken=next_page_token
                )
                response=request.execute()

                for item in response['items']:
                        data=dict(Playlist_Id=item['id'],
                                Title=item['snippet']['title'],
                                Channel_Id=item['snippet']['channelId'],
                                Channel_Name=item['snippet']['channelTitle'],
                                PublishedAt=item['snippet']['publishedAt'],
                                Video_Count=item['contentDetails']['itemCount'])
                        All_data.append(data)

                next_page_token=response.get('nextPageToken')
                if next_page_token is None:
                        break
        return All_data



def get_channel_details(channel_id):
    channel_details = get_channel_info(channel_id)
    playlist_details = get_playlist_details(channel_id)
    video_ids = get_videos_ids(channel_id)
    video_details = get_video_info(video_ids)
    comment_details = get_comment_info(video_ids)

    channel_df = pd.DataFrame([channel_details])
    playlist_df = pd.DataFrame(playlist_details)
    video_details_df = pd.DataFrame(video_details)
    comment_df = pd.DataFrame(comment_details)

    return {
        "channel_details" : channel_df,
        "playlist_details" :playlist_df,
        "video_details" : video_details_df,
        "comment_details" : comment_df
     }




#table creation in sql
import MySQLdb


mydb = MySQLdb.connect(
  host="localhost",
  user="root",
  password="root",
  database="youtube_app"
)

mycursor = mydb.cursor()



# Create table for channel details
mycursor.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        Channel_Name VARCHAR(255),
        Channel_Id VARCHAR(255) PRIMARY KEY,
        Subscribers INT,
        Views INT,
        Total_Videos INT,
        Channel_Description TEXT,
        Playlist_Id VARCHAR(255)
    )
""")

# Create table for playlist details
mycursor.execute("""
    CREATE TABLE IF NOT EXISTS playlists (
        Playlist_Id VARCHAR(255) PRIMARY KEY,
        Title VARCHAR(255),
        Channel_Id VARCHAR(255),
        Channel_Name VARCHAR(255),
        PublishedAt DATETIME,
        Video_Count INT
    )
""")

# Create table for video details
mycursor.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        Channel_Name VARCHAR(255),
        Channel_Id VARCHAR(255),
        Video_Id VARCHAR(255) PRIMARY KEY,
        Title VARCHAR(255),
        Tags TEXT,
        Thumbnail VARCHAR(255),
        Description TEXT,
        Published_Date DATETIME,
        Duration VARCHAR(255),
        Views INT,
        Likes INT,
        Comments INT,
        Favorite_Count INT,
        Definition VARCHAR(10),
        Caption_Status VARCHAR(50)
    )
""")

# Create table for comment details
mycursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        Comment_Id VARCHAR(255) PRIMARY KEY,
        Video_Id VARCHAR(255),
        Comment_Text TEXT,
        Comment_Author VARCHAR(255),
        Comment_Published DATETIME
    )
""")

mydb.commit()



# List of channel IDs
channel_ids = ["UCxpoRU4Q0f482LTz6beHoHA", "UCiDVY034k3QcUjADMeEJ2QQ",
               "UCDJWKNWDcD6A4K_4xNUmZVQ", "UCLL4MEFbPNar-rlrodsRSog",
               "UCduIoIMfD8tT3KoU0-zBRgQ", "UCwr-evhuzGZgDFrq_1pLt_A",
               "UCuI5XcJYynHa5k_lqDzAgwQ", "UCyvImezzbr4RQVFOmL7KfZg",
               "UC3vBxF1ewR-W-9yIO0xiHfg", "UC27RVF0t6IPbup0MnUoTmzw"]

def insert_multiple_channel_details(channel_ids):
    for channel_id in channel_ids:
        mycursor.execute("SELECT Channel_Id FROM channels WHERE Channel_Id = %s", (channel_id,))
        existing_channel = mycursor.fetchone()

        if existing_channel:
            print(f"Channel with ID {channel_id} already exists in the table.")
        else:
            channel_data = get_channel_info(channel_id)
            if channel_data:
                sql = """
                    INSERT INTO channels 
                    (Channel_Name, Channel_Id, Subscribers, Views, Total_Videos, Channel_Description, Playlist_Id) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    channel_data['Channel_Name'],
                    channel_data['Channel_Id'],
                    channel_data['Subscribers'],
                    channel_data['Views'],
                    channel_data['Total_Videos'],
                    channel_data['Channel_Description'],
                    channel_data['Playlist_Id']
                )
                mycursor.execute(sql, values)
                mydb.commit()
                print(f"Channel with ID {channel_id} inserted successfully.")
            else:
                print(f"Channel with ID {channel_id} not found or data retrieval failed.")









def insert_multiple_playlist_details(channel_ids):
    for channel_id in channel_ids:
        playlist_details = get_playlist_details(channel_id)
        
        for playlist_data in playlist_details:
            # Convert 'PublishedAt' datetime string to MySQL TIMESTAMP format
            published_at = datetime.strptime(playlist_data['PublishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')

            mycursor.execute("SELECT Playlist_Id FROM playlists WHERE Playlist_Id = %s", (playlist_data['Playlist_Id'],))
            existing_playlist = mycursor.fetchone()

            if existing_playlist:
                print(f"Playlist with ID {playlist_data['Playlist_Id']} already exists in the table.")
            else:
                sql = """
                    INSERT INTO playlists 
                    (Playlist_Id, Title, Channel_Id, Channel_Name, PublishedAt, Video_Count) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                values = (
                    playlist_data['Playlist_Id'],
                    playlist_data['Title'],
                    playlist_data['Channel_Id'],
                    playlist_data['Channel_Name'],
                    published_at,  # Use the converted datetime value
                    playlist_data['Video_Count']
                )
                mycursor.execute(sql, values)
                mydb.commit()
                print(f"Playlist with ID {playlist_data['Playlist_Id']} inserted successfully.")







from datetime import datetime

def insert_multiple_video_details(channel_ids):
    for channel_id in channel_ids:
        video_ids = get_videos_ids(channel_id)
        
        video_details = get_video_info(video_ids)
        
        for video_data in video_details:
            published_date = datetime.strptime(video_data['Published_Date'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')



            mycursor.execute("SELECT Video_Id FROM videos WHERE Video_Id = %s", (video_data['Video_Id'],))
            existing_video = mycursor.fetchone()

            if existing_video:
                print(f"Video with ID {video_data['Video_Id']} already exists in the table.")
            else:
                sql = """
                    INSERT INTO videos 
                    (Channel_Name,
                    Channel_Id,
                    Video_Id, 
                    Title, Tags,
                    Thumbnail,
                    Description,
                    Published_Date,
                    Duration, Views,
                    Likes, Comments,
                    Favorite_Count,
                    Definition,
                    Caption_Status) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    video_data['Channel_Name'],
                    video_data['Channel_Id'],
                    video_data['Video_Id'],
                    video_data['Title'],
                    ','.join(video_data['Tags']) if video_data['Tags'] else None,
                    video_data['Thumbnail'],
                    video_data['Description'],
                    published_date,
                    video_data['Duration'],
                    video_data['Views'],
                    video_data['Likes'],
                    video_data['Comments'],
                    video_data['Favorite_Count'],
                    video_data['Definition'],
                    video_data['Caption_Status']
                )
                mycursor.execute(sql, values)
                mydb.commit()

                print(f"Video with ID {video_data['Video_Id']} inserted successfully.")




from datetime import datetime

def insert_multiple_comment_details(channel_ids):
    for channel_id in channel_ids:
        video_ids = get_videos_ids(channel_id)
        comment_details = get_comment_info(video_ids)
        
        for comment_data in comment_details:
            mycursor.execute("SELECT Comment_Id FROM comments WHERE Comment_Id = %s", (comment_data['Comment_Id'],))
            existing_comment = mycursor.fetchone()

            if existing_comment:
                print(f"Comment with ID {comment_data['Comment_Id']} already exists in the table.")
            else:
                # Convert 'Comment_Published' datetime string to MySQL TIMESTAMP format
                comment_published = datetime.strptime(comment_data['Comment_Published'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')

                sql = """
                    INSERT INTO comments 
                    (Comment_Id, Video_Id, Comment_Text, Comment_Author, Comment_Published) 
                    VALUES (%s, %s, %s, %s, %s)
                """
                values = (
                    comment_data['Comment_Id'],
                    comment_data['Video_Id'],
                    comment_data['Comment_Text'],
                    comment_data['Comment_Author'],
                    comment_published  # Use the converted datetime value
                )
                mycursor.execute(sql, values)
                mydb.commit()
                print(f"Comment with ID {comment_data['Comment_Id']} inserted successfully.")








# Function to fetch data from the channels table and create a DataFrame
def get_channels_df():
    mycursor.execute("SELECT * FROM channels")
    data = mycursor.fetchall()
    columns = [desc[0] for desc in mycursor.description]
    df = pd.DataFrame(data, columns=columns)

    return df

# Function to fetch data from the playlists table and create a DataFrame
def get_playlists_df():
    mycursor.execute("SELECT * FROM playlists")
    data = mycursor.fetchall()
    columns = [desc[0] for desc in mycursor.description]
    df1 = pd.DataFrame(data, columns=columns)

    return df1

# Function to fetch data from the videos table and create a DataFrame
def get_videos_df():
    mycursor.execute("SELECT * FROM videos")
    data = mycursor.fetchall()
    columns = [desc[0] for desc in mycursor.description]
    df2 = pd.DataFrame(data, columns=columns)

    return df2


# Function to fetch data from the comments table and create a DataFrame
def get_comments_df():
    mycursor.execute("SELECT * FROM comments")
    data = mycursor.fetchall()
    columns = [desc[0] for desc in mycursor.description]
    df3 = pd.DataFrame(data, columns=columns)

    return df3

# Sample usage:
channels_df = get_channels_df()
playlists_df = get_playlists_df()
videos_df = get_videos_df()
comments_df = get_comments_df()




#======================================================= STREAMLIT PART =========================================================================#

# Streamlit Part


mydb = MySQLdb.connect(
  host="localhost",
  user="root",
  password="root",
  database="youtube_app"
)

mycursor = mydb.cursor()

def show_channels_table():
    mycursor.execute("SELECT * FROM channels")
    data = mycursor.fetchall()
    columns = [desc[0] for desc in mycursor.description]
    df = pd.DataFrame(data, columns=columns)
    st.write(df)

def show_playlists_table():
    mycursor.execute("SELECT * FROM playlists")
    data = mycursor.fetchall()
    columns = [desc[0] for desc in mycursor.description]
    df1 = pd.DataFrame(data, columns=columns)
    st.write(df1)

def show_videos_table():
    mycursor.execute("SELECT * FROM videos")
    data = mycursor.fetchall()
    columns = [desc[0] for desc in mycursor.description]
    df2 = pd.DataFrame(data, columns=columns)
    st.write(df2)

def show_comments_table():
    mycursor.execute("SELECT * FROM comments")
    data = mycursor.fetchall()
    columns = [desc[0] for desc in mycursor.description]
    df3 = pd.DataFrame(data, columns=columns)
    st.write(df3)


st.set_page_config(layout="wide")
st.title(":red[YOUTUBE DATA HARVESTING AND WAREHOUSING]")

with st.sidebar:
    select = option_menu("MAIN MENU",['HOME' ,"EXTRACTION AND TRANSFORM","SQL DATABASE" , "VIEW"])

# MySQL database connection
mydb = MySQLdb.connect(
  host="localhost",
  user="root",
  password="root",
  database="youtube_app"
)
mycursor = mydb.cursor()

# Function to execute SQL queries and return DataFrame
def execute_query(query):
    mycursor.execute(query)
    data = mycursor.fetchall()
    columns = [desc[0] for desc in mycursor.description]
    df = pd.DataFrame(data, columns=columns)
    return df

if select == "HOME":
    st.image("youtube_logo.png", width=400)
    st.markdown("---")
    st.write("Welcome to YouTube Data Harvesting and Warehousing!")
    st.write("  - YESWANTH KUMAR R")
    st.markdown("---")
    st.write("This platform allows you to extract, transform, and view YouTube data.")
    st.write("Use the sidebar to navigate through different sections.")
    st.markdown("---")

elif select == "EXTRACTION AND TRANSFORM":
    st.subheader("Extract Data for Specific Channel")
    channel_id = st.text_input("Enter Channel ID:")
    if st.button("Extract Data"):
        if channel_id:
            try:
                insert_multiple_channel_details([channel_id])
                insert_multiple_playlist_details([channel_id])
                insert_multiple_video_details([channel_id])
                insert_multiple_comment_details([channel_id])
                st.success("Data extraction successful!")
            except Exception as e:
                st.error(f"Error occurred: {e}")
        else:
            st.warning("Please enter a valid Channel ID.")

    # Display tables after data extraction
    if st.checkbox("Show Extracted Data"):
        channels_df = get_channels_df()
        playlists_df = get_playlists_df()
        videos_df = get_videos_df()
        comments_df = get_comments_df()

        # Filter data frames to show only relevant information
        channel_data = channels_df[channels_df['Channel_Id'] == channel_id]
        playlist_data = playlists_df[playlists_df['Channel_Id'] == channel_id]
        video_data = videos_df[videos_df['Channel_Id'] == channel_id]
        comment_data = comments_df[comments_df['Video_Id'].isin(video_data['Video_Id'])]

        st.subheader("Channel Details")
        st.write(channel_data)

        st.subheader("Playlist Details")
        st.write(playlist_data)

        st.subheader("Video Details")
        st.write(video_data)

        st.subheader("Comment Details")
        st.write(comment_data)


elif select == "SQL DATABASE":
    # Fetch all channel names from the 'channels' table
    mycursor.execute("SELECT Channel_Name FROM channels")
    channels_data = mycursor.fetchall()
    channel_names = [channel[0] for channel in channels_data]

    # Create a dropdown to select a channel name
    selected_channel = st.selectbox("Select a Channel Name:", channel_names)

    if selected_channel:
        # Fetch data for the selected channel from respective tables
        mycursor.execute("SELECT * FROM channels WHERE Channel_Name = %s", (selected_channel,))
        channel_data = mycursor.fetchall()
        st.subheader("Channel Details")
        st.write(pd.DataFrame(channel_data, columns=[desc[0] for desc in mycursor.description]))

        mycursor.execute("SELECT * FROM playlists WHERE Channel_Name = %s", (selected_channel,))
        playlists_data = mycursor.fetchall()
        st.subheader("Playlist Details")
        st.write(pd.DataFrame(playlists_data, columns=[desc[0] for desc in mycursor.description]))

        mycursor.execute("SELECT * FROM videos WHERE Channel_Name = %s", (selected_channel,))
        videos_data = mycursor.fetchall()
        st.subheader("Video Details")
        st.write(pd.DataFrame(videos_data, columns=[desc[0] for desc in mycursor.description]))

        mycursor.execute("SELECT * FROM comments WHERE Video_Id IN (SELECT Video_Id FROM videos WHERE Channel_Name = %s)", (selected_channel,))
        comments_data = mycursor.fetchall()
        st.subheader("Comment Details")
        st.write(pd.DataFrame(comments_data, columns=[desc[0] for desc in mycursor.description]))



elif select == "VIEW":
    # 10 Questions
    questions = [
        "All the videos and the channel name",
        "Channels with the most number of videos",
        "10 most viewed videos",
        "Comments in each video",
        "Videos with the highest likes",
        "Likes of all videos",
        "Views of each channel",
        "Videos published in the year 2022",
        "Average duration of all videos in each channel",
        "Videos with the highest number of comments"
    ]
    selected_question = st.selectbox("Select a Question:", questions)

    if selected_question:
        # Execute respective SQL queries based on the selected question
        if selected_question == questions[0]:
            query = "SELECT Channel_Name, Title FROM videos"
        elif selected_question == questions[1]:
            query = "SELECT Channel_Name, COUNT(*) AS Video_Count FROM videos GROUP BY Channel_Name ORDER BY Video_Count DESC LIMIT 1"
        elif selected_question == questions[2]:
            query = "SELECT Title, Views FROM videos ORDER BY Views DESC LIMIT 10"
        elif selected_question == questions[3]:
            query = "SELECT Video_Id, COUNT(*) AS Comment_Count FROM comments GROUP BY Video_Id"
        elif selected_question == questions[4]:
            query = "SELECT Title, Likes FROM videos ORDER BY Likes DESC LIMIT 1"
        elif selected_question == questions[5]:
            query = "SELECT Title, Likes FROM videos"
        elif selected_question == questions[6]:
            query = "SELECT Channel_Name, SUM(Views) AS Total_Views FROM videos GROUP BY Channel_Name"
        elif selected_question == questions[7]:
            query = "SELECT Title, Published_Date FROM videos WHERE YEAR(Published_Date) = 2022"
        elif selected_question == questions[8]:
            query = "SELECT Channel_Name, AVG(Duration) AS Avg_Duration FROM videos GROUP BY Channel_Name"
        elif selected_question == questions[9]:
            query = "SELECT Title, Comments FROM videos ORDER BY Comments DESC LIMIT 1"

        result_df = execute_query(query)
        st.subheader(selected_question)
        st.write(result_df)
