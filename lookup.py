from asyncio import run as async_run
import os
from sys import argv
import subprocess
from aiohttp import ClientSession
from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.authentication.models import OAuth2TokenResponse
import argparse
from dotenv import load_dotenv

async def retrieve(xuids, gamertags, client_id, client_secret, xtoken):
    global session
    auth = AuthenticationManager(session, client_id, client_secret, "")
    await freshen_tokens(auth, xtoken)
    client = XboxLiveClient(auth)

    retrieved_xuids = []
    retrieved_gamertags = []

    # Loop through gamertags
    for gt in gamertags:
        # Get profile from gamertag
        profile = await client.profile.get_profile_by_gamertag(gt)
        # Get ID from profile and append to list
        retrieved_xuids.append(int(profile.profile_users[0].id))
    # Loop though XUIDs
    for x in xuids:
        # Get profile from XUID
        profile = await client.profile.get_profile_by_xuid(x)
        # Get gamertag from profile and append to list
        # Gamertag is stored in the first entry of settings
        # This gets the value of the first entry in settings
        retrieved_gamertags.append(profile.profile_users[0].settings[0].value)
    # Return as a tuple
    # TODO
    # Find a better way to do this
    return (retrieved_xuids, retrieved_gamertags)

# Refresh tokens.json
async def freshen_tokens(auth_mgr, token_jar):
    with open(token_jar, "r+") as f:
        auth_mgr.oauth = OAuth2TokenResponse.parse_raw(f.read())
        await auth_mgr.refresh_tokens()
        f.seek(0)
        f.truncate()
        f.write(auth_mgr.oauth.json())

# Main async function 
# Can be called from outsidde script if all arguments are given
async def async_main(xuids, gamertags, client_id, client_secret, xtoken):
    global session
    subprocess.run(["xbox-authenticate"], check=True)
    async with ClientSession() as session:
        return await retrieve(xuids, gamertags, client_id, client_secret, xtoken)

# If script is ran from command line
# Requires arguments
# 
if __name__ == '__main__':
    # Load environment variables from .env
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("-x", "--xuids", help="Comma separated list of XUIDs to retrieve gamertags from")
    parser.add_argument("-g", "--gamertags", help="Comma separated list of gamertags to retrieve XUIDs from")
    parser.add_argument("-i", "--id", help="Client ID to authenticate with")
    parser.add_argument("-s", "--secret", help="Client secret to authenticate with")
    parser.add_argument("-X", "--xtoken", help="Path to tokens.json file")
    args = parser.parse_args()
    # If ID wasn't given as argument, try to retrieve from environment
    if not args.id:
        args.id = os.getenv("CLIENT_ID")
    # If secret wasn't given as argument, try to retrieve from environment
    if not args.secret:
        args.secret = os.getenv("CLIENT_SECRET")
    if not args.xtoken:
        args.xtoken = os.path.join(os.getenv("HOME"), ".local", "share", "xbox", "tokens.json")

    # Check if XUIDs or gamertags are given
    if not args.xuids and not args.gamertags:
        print("Can not continue without any XUIDs or gamertags")
        exit(1)
    # Set empty lists for if argument isn't given
    xuids = []
    gamertags = []
    # Fill lists with given arguments
    if args.xuids:
        xuids = args.xuids.split(",")
    if args.gamertags:
        gamertags = args.gamertags.split(",")
    
    print("Input gamertags: ", gamertags)
    print("Input XUIDs: ", xuids)

    tuple = async_run(async_main(xuids, gamertags, args.id, args.secret, args.xtoken))

    print("Retrieved XUIDs: ", tuple[0])
    print("Retrieved gamertags: ", tuple[1])