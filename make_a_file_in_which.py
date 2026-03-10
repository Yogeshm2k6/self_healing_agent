import requests
import json
import os

# Instagram API endpoint and access token
endpoint = "https://graph.instagram.com/v13.0"
access_token = "YOUR_ACCESS_TOKEN"

# Define the function to collect posts
def collect_posts(username, num_posts):
    try:
        # Set the API endpoint and parameters
        url = f"{endpoint}/{username}/media"
        params = {
            "fields": "id,caption,media_url,thumbnail_url",
            "access_token": access_token,
            "limit": num_posts
        }

        # Send the GET request
        response = requests.get(url, params=params)

        # Check if the request was successful
        response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        # Create a list to store the posts
        posts = []

        # Loop through the data and extract the posts
        for post in data["data"]:
            post_data = {
                "id": post["id"],
                "caption": post.get("caption", ""),
                "media_url": post["media_url"],
                "thumbnail_url": post.get("thumbnail_url", "")
            }
            posts.append(post_data)

        # Return the list of posts
        return posts
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}"
    except requests.exceptions.ConnectionError as conn_err:
        return f"Error connecting to the API: {conn_err}"
    except requests.exceptions.Timeout as time_err:
        return f"Timeout error occurred: {time_err}"
    except requests.exceptions.RequestException as err:
        return f"Something went wrong: {err}"
    except json.JSONDecodeError as json_err:
        return f"Failed to parse JSON: {json_err}"
    except KeyError as key_err:
        return f"Missing key in JSON response: {key_err}"

# Define the function to save posts to a file
def save_posts_to_file(posts, filename):
    try:
        # Create a dictionary to store the posts
        data = {
            "posts": posts
        }

        # Open the file and write the data
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
    except OSError as os_err:
        print(f"Error writing to file: {os_err}")
    except Exception as err:
        print(f"An error occurred: {err}")

# Example usage
username = "example_username"
num_posts = 10
filename = "instagram_posts.json"

# Collect the posts
posts = collect_posts(username, num_posts)

# Save the posts to a file
if isinstance(posts, list):
    save_posts_to_file(posts, filename)
    print(f"Posts saved to {filename}")
    
    # Print the contents of the file
    try:
        with open(filename, "r") as file:
            print(file.read())
    except OSError as os_err:
        print(f"Error reading from file: {os_err}")
else:
    print(posts)
    print(f"Skipping file read because posts were not collected.")