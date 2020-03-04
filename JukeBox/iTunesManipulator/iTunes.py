import os, sys
import vlc
import time
import random
import glob
from Youtube import Youtube
from speechPrompts import computer
from Player import jukebox
from iTunesManipulator import iTunesSearch
from Features import tools
import GlobalVariables


"""
Checks computers iTunes to see if it is installed
args: iTunes song paths dict, autodownload mode enabled, speech recognition mode enabled,
      path to root script folder, speech recognition command, microphone object,
      speech recognition object
Return: True is song is found/research/skip, else false
 """
def check_iTunes_for_song(iTunesPaths,
                          autoDownload,
                          speechRecogOn=None,
                          pathToDirectory='',
                          command='',
                          mic=None,
                          r=None):
    artists = [] # will hold list of artists
    songNames = [] # need to be zeroed out here DO NOT MOVE into parameter.
    albums = []
    songSelection = ''
    if len(iTunesPaths['searchedSongResult']) == 0:
        print("File not found in iTunes Library.. Searching iTunes API")
        return False
    else:
        # get the first item of the songs returned from the list of song paths matching
        # plays song immediatly, so return after this executes
        print("Here are song(s) in your library matching your search: ")
        i = 0

        for songPath in iTunesPaths['searchedSongResult']:
            songName = songPath.split(os.sep)
            artists.append(songName[len(songName)-3])
            albums.append(songName[len(songName)-2])
            songNames.append(songName[len(songName)-1])
            print('  %d \t- %s - %s: %s' % (i, albums[i], artists[i], songNames[i]))
            i += 1

        # autoDownload condition
        if autoDownload == True:
            print("Song name too similar to one or more of above! Skipping.")
            return True

        if speechRecogOn == False:
            print('Which one(s) do you want to hear (e.g. 0 1 3)?')
            user_input_string = "OR type 'se' (perform search), 'ag' (search again/skip), 'sh' (shuffle), 'pl' (play in order), '406' (return home): "
            songSelection = iTunesSearch.choose_items(input_string=user_input_string, props_lyst=iTunesPaths['searchedSongResult'])

        if speechRecogOn == True and command == 'shuffle':
            songSelection = 'sh'

        elif speechRecogOn == True and command == 'play':
            songSelection = 'pl'

        elif speechRecogOn == True and command == 'single':
            iTunesPaths['searchedSongResult'] = [iTunesPaths['searchedSongResult'][0]] # select first song, data requires list
            play_in_order(iTunesPaths, speechRecogOn, pathToDirectory, "Single Mode Activated", 'singleModeOn.m4a', mic=mic, r=r)
            return True
        if songSelection == 'ag':
            print('Returning to beginning.')
            return True
        if songSelection == GlobalVariables.quit_string:
            print("Exiting to home.")
            return GlobalVariables.quit_string

        # shuffle algorithm TODO: move to a function
        if songSelection == 'sh':
            random.shuffle(iTunesPaths['searchedSongResult'])
            play_in_order(iTunesPaths, speechRecogOn, pathToDirectory, "Shuffle Mode Activated", 'shuffleModeOn.m4a', mic=mic, r=r)
            return True

        elif songSelection == 'se':
            return False

        elif songSelection == 'pl':
            play_in_order(iTunesPaths, speechRecogOn, pathToDirectory, "Ordered Mode Activated", 'orderModeOn.m4a', mic=mic, r=r)
            return True

        # play the song(s) only if they want, otherwise continute with program.
        else:
            if speechRecogOn == False:
                iTunesPaths['searchedSongResult'] = songSelection
                play_in_order(iTunesPaths, speechRecogOn, pathToDirectory, mic=mic, r=r)

            return True

"""
Begins playing through a list of songs in order
args: iTunes song paths dict, speech recognition command, path to root script folder,
      output speech text, audiofile path for speech prompt (windows), microphone object,
      speech recognizer object
Returns: None
"""
def play_in_order(iTunesPaths, speechRecogOn, pathToDirectory, speech_string='', speech_path='', mic=None, r=None):

    wait_until_end = ''
    if speechRecogOn == True:
        computer.speak(sys.platform,
                       speech_string,
                       os.path.join(pathToDirectory, 'speechPrompts', speech_path)
                       )
    print(GlobalVariables.PLAYING_STRING_COMMANDS_DEFAULT) # provide commands
    i = 0
    while i < len(iTunesPaths['searchedSongResult']):
        song = iTunesPaths['searchedSongResult'][i].split(os.sep)
        if speechRecogOn == True:
            computer.speak(sys.platform,
                           "Playing: %s." % (tools.stripFileForSpeech(song[len(song)-1])),
                           os.path.join(pathToDirectory, 'speechPrompts', 'playingSong.m4a')
                           )
        wait_until_end = jukebox.play_file(GlobalVariables.PLAYING_STRING_DEFAULT % (song[len(song)-3], #3 is album
                                                                                     song[len(song)-2], #2 is artist
                                                                                     song[len(song)-1]), #1 is song
                                                                                     iTunesPaths['searchedSongResult'][i],
                                                                                     song_index=i,
                                                                                     index_diff=len(iTunesPaths['searchedSongResult'])-i,
                                                                                     mic=mic, r=r, speechRecogOn=speechRecogOn,
                                                                                     command_string=GlobalVariables.PLAYING_STRING_COMMANDS_SPECIAL)
        if wait_until_end == 'rewind' and i != 0: # break loop if user desires it to be.
            i = i-1 # play previous

        if wait_until_end == 'next':
            i = i+1 # play next song
        if wait_until_end == GlobalVariables.player_stop: # break loop if user desires it to be.
            break # quit

"""
Determines whether iTunes is installed on the computer, and generates path to
the automatically add to iTunes folder
args: operating system from sys.platform, iTunesPaths dictionary object, song to search iTunes for
Returns: object with path to automatically add to iTunes folder and songs matching
         user's search
"""
def setItunesPaths(operatingSystem, iTunesPaths={'autoAdd':'', 'searchedSongResult':[]}, searchFor=''):
    iTunesPaths['searchedSongResult'] = []
    if operatingSystem == 'darwin':
        pathToItunesAutoAdd = os.path.join('/Users', '*', 'Music', 'iTunes', 'iTunes Media', 'Automatically Add to Music.localized')
        pathToSong = os.path.join('/Users', '*', 'Music', 'iTunes', 'iTunes Media', 'Music', '*', '*','*.*')
    elif operatingSystem == 'win32':
        pathToItunesAutoAdd = os.path.join('C:', os.sep, 'Users', '*', 'Music', 'iTunes', 'iTunes Media', 'Automatically Add to iTunes')
        pathToSong = os.path.join('C:', os.sep, 'Users', '*', 'Music', 'iTunes', 'iTunes Media', 'Music', '*', '*', '*.*')
    else:
        print("Unrecognized OS. No Itunes recognizable.")
        return None
    addToItunesPath = glob.glob(pathToItunesAutoAdd, recursive=True)

    if len(addToItunesPath) == 0:
        print('You do not have iTunes installed on this machine. Continueing without.')
        return None

    iTunesPaths['autoAdd'] = addToItunesPath[0]
    # '*.*' means anyfilename, anyfiletype
    # /*/* gets through artist, then album or itunes folder structure
    # iTUNES LIBRARY SEARCH ALGORITHM -- returns lists of matches
    path = glob.glob(pathToSong, recursive=True)
    iTunesPaths = iTunesLibSearch(songPaths=path, iTunesPaths=iTunesPaths, searchParameters=searchFor)
    return iTunesPaths

"""
Performs a search on users iTunes library by album, artist and genre
args: paths to all iTunes songs, iTunes dictionary object, search term
Returns: iTunesPaths dict with songs matching the search added 
"""
def iTunesLibSearch(songPaths, iTunesPaths={}, searchParameters=''):

    for songPath in songPaths:
        songNameSplit = songPath.split(os.sep)
        formattedName = songNameSplit[len(songNameSplit)-1].lower() + " " + songNameSplit[len(songNameSplit)-2].lower() + " " + songNameSplit[len(songNameSplit)-3].lower()
        formattedName = Youtube.removeIllegalCharacters(formattedName)
        searchParameters = Youtube.removeIllegalCharacters(searchParameters)
        # songNameSplit is list of itunes file path.. artist is -3 from length, song is -1
        if searchParameters.lower() in formattedName.lower():
            iTunesPaths['searchedSongResult'].append(songPath)
    iTunesPaths['searchedSongResult'] = sorted(iTunesPaths['searchedSongResult']) # sort tracks alphabetically
    return iTunesPaths
