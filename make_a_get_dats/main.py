from pytube import YouTube

def get_video_data(url):
    """
    Get video data from YouTube.
    
    Args:
        url (str): YouTube video URL.
    
    Returns:
        dict: Video data.
    """
    yt = YouTube(url)
    data = {
        "title": yt.title,
        "author": yt.author,
        "length": yt.length,
        "views": yt.views,
        "rating": yt.rating,
        "description": yt.description,
    }
    return data

def get_channel_data(url):
    """
    Get channel data from YouTube.
    
    Args:
        url (str): YouTube channel URL.
    
    Returns:
        dict: Channel data.
    """
    # Note: pytube does not support getting channel data directly.
    # You may need to use the YouTube API for this.
    # For simplicity, we will just return an empty dictionary.
    return {}

def main():
    url = input("Enter YouTube video or channel URL: ")
    if "watch" in url:
        data = get_video_data(url)
        print("Video Data:")
        for key, value in data.items():
            print(f"{key}: {value}")
    else:
        data = get_channel_data(url)
        print("Channel Data:")
        for key, value in data.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    main()
