Program to calculate stream times and compare those times to HowLongToBeats average main story clear time   
Currently works only on unix systems as it uses shlex. "The shlex module is only designed for Unix shells." (shlex documentation)[https://docs.python.org/3/library/shlex.html]
   
Files names in 'finished' directory are game ids that Twitch uses.   
Files that only have minutes in them could be inaccurate as i haven't had the time to go through all of them induvitually, but rather just used a script to gather them in one file.   
Data used in these files was gotten from (sullygnome)[https://sullygnome.com/]. Big thanks to who runs that site, has been massive help on this and other projects.   
   
To use this you will also need a database which contains Twitch game data, which isn't provided in this repository   
I have it named just game_ids.db which uses (Sqlite3)[https://www.sqlite.org/index.html]
