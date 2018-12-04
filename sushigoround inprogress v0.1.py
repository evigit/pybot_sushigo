#! python3
"""Sushi Go ROund Bot
Al Sweigart al@inventwithpython.com @AlSweigart

A Bot program to automatically play the Sushi Go Round flash game at http://miniclip.com/games/sushi-go-round/en/
"""

import pyautogui, time, os, logging, sys, random, copy
# PyAutoGUI provides basic image recognition by finding the screen coordinates of a provided image.

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d: %(message)s', datefmt='%H:%M:%S')
# logging.disable(logging.DEBUG) # uncomment to block debug log messages

# This generic code sets up a shebang line, some comments to describe the program, imports for several modules,
# and setting up logging so that the logging.debug() function will output debug messages.
# (I explain why logging is preferable to print() calls in this blog post.


# Food order constants (these values depending on image filenames)
#  last -tuple of all food orders

ONIGIRI = 'onigiri'
CALIFORNIA_ROLL = 'california_roll'
GUNKAN_MAKI = 'gunkan maki'
SALMON_ROLL = 'salmon_roll'
SHRIMP_SUSHI = 'shrimp_sushi'
UNAGI_ROLL = 'unagi_roll'
DRAGON_ROLL = 'dragon_roll'
COMBO = 'combo'
ALL_ORDER_TYPES = (ONIGIRI, CALIFORNIA_ROLL, GUNKAN_MAKI, SALMON_ROLL,
                   SHRIMP_SUSHI, UNAGI_ROLL, DRAGON_ROLL, COMBO)

# Ingredient constants (these values depending on image filenames)
#  last - tuple of all ingredients

SHRIMP = 'shrimp'
RICE = 'rice'
NORI = 'nori'
ROE = 'roe'
SALMON = 'salmon'
UNAGI = 'unagi'
RECIPE = {ONIGIRI:          {RICE: 2, NORI: 1},
          CALIFORNIA_ROLL:  {RICE: 1, NORI: 1, ROE: 1},
          GUNKAN_MAKI:      {RICE: 1, NORI: 1, ROE: 2},
          SALMON_ROLL:      {RICE: 1, NORI: 1, SALMON: 2},
          SHRIMP_SUSHI:     {RICE: 1, NORI: 1, SHRIMP: 2},
          UNAGI_ROLL:       {RICE: 1, NORI: 1, UNAGI: 2},
          DRAGON_ROLL:      {RICE: 2, NORI: 1, ROE: 1, UNAGI: 2},
          COMBO:            {RICE: 2, NORI: 1, ROE: 1, SALMON: 1, UNAGI: 1, SHRIMP: 1}, }

# checkForGameOver() returns this value if the level has been won
LEVEL_WIN_MESSAGE = 'win'

# Settings
MIN_INGREDIENTS = 4     # if an ingredient gets below this value, order more
PLATE_CLEARING_FREQ = 8 # plates are cleared every this number of seconds (roughly)
NORMAL_RESTOCK_TIME = 7 # restock inventory cooldown(at normal speed, not express)
TIME_TO_REMAKE = 30     # if an order goes unfilled for this number of seconds, remake it

# Global variables
LEVEL = 1 # current level being played
INVENTORY = {SHRIMP: 5, RICE: 10,
             NORI: 10, ROE: 10,
             SALMON: 5, UNAGI: 5}
GAME_REGION = () # (left, top, width, height) values coordinates of the game window
ORDERING_COMPLETE = {SHRIMP: None, RICE: None, NORI: None, ROE: None, SALMON: None, UNAGI: None}
# unix timestamp when an ordered ingredient will have arrived
ROLLING_COMPLETE = 0 # unix timestamp of when the rolling of the mat will have completed
LAST_PLATE_CLEARING = 0 # unix timestamp of the last time the plates were cleared
LAST_GAME_OVER_CHECK = 0 # unix timestamp when it last checked for "You win" msgs


# various cooridnates of objects in the game for setupCoordinates() function
GAME_REGION = () # (left, top, width, height) values coordinates of the entire game window
INGRED_COORDS = None
PHONE_COORDS = None
TOPPING_COORDS = None
ORDER_BUTTON_COORDS = None
RICE1_COORDS = None
RICE2_COORDS = None
NORMAL_DELIVERY_BUTTON_COORDS = None
MAT_COORDS = None

#function
def main():
    """Runs the entire program. The Sushi Go Round Game must be visible on the screen and PLAY button visible."""
    logging.debug('Program Started. Press Ctrl+C to abort at any time.')
    logging.debug('To interrupt mouse movement, move mouse to upper left corner.')
    getGameRegion()
    navigateStartGameMenu()
    setupCoordinates()
    startServing()


def imPath(filename):
    """A shortcut for joining the 'images/'' file path. Returns the filename with 'images/' prepended."""
    return os.path.join('images', filename)

# about GAME_REGION (left, top, width, height) variable:
# The "left" value is the X-coordinate of the left edge, the "top" value is the Y-coordinate of the top edge.
# With the XY coordinates of the top-left corner and the width and height, you can completely describe the region.

def getGameRegion():
    """Obtains the region that the Sushi Go Round game is on the screen and assigns"""
    global GAME_REGION

    # identify the top-left corner
    logging.debug('Finding game region...')
    region = pyautogui.locateOnScreen(imPath('top_right_corner.png'))
    if region is None:
        raise Exception('Could not find game on screen. Is the game visible?')

    # calculate the region of the entire game
    topRightX = region[0] + region[2] # left + width
    topRightY = region[1] # top
    GAME_REGION = (topRightX - 640, topRightY, 640, 480) # the game screen is always 640 x 480
    logging.debug('Game region found: %s' % (GAME_REGION,))


#Coordinates can be displayed with pyautogui.displayMousePosition()
def setupCoordinates():
    """Sets several of the coordinate-related global variables, after acquiring the value for GAME_REGION."""
    global INGRED_COORDS, PHONE_COORDS, TOPPING_COORDS, ORDER_BUTTON_COORDS, RICE1_COORDS, RICE2_COORDS,\
            NORMAL_DELIVERY_BUTTON_COORDS, MAT_COORDS, LEVEL
    INGRED_COORDS = {SHRIMP:    (GAME_REGION[0] + 40, GAME_REGION[1] + 335),
                     RICE:      (GAME_REGION[0] + 95, GAME_REGION[1] + 335),
                     NORI:      (GAME_REGION[0] + 40, GAME_REGION[1] + 385),
                     ROE:       (GAME_REGION[0] + 95, GAME_REGION[1] + 385),
                     SALMON:    (GAME_REGION[0] + 40, GAME_REGION[1] + 425),
                     UNAGI:     (GAME_REGION[0] + 95, GAME_REGION[1] + 425),}
    PHONE_COORDS = (GAME_REGION[0] + 560, GAME_REGION[1] + 360)
    TOPPING_COORDS = (GAME_REGION[0] + 513, GAME_REGION[1] + 269)
    ORDER_BUTTON_COORDS = {SHRIMP:  (GAME_REGION[0] + 496, GAME_REGION[1] + 222),
                           UNAGI:   (GAME_REGION[0] + 578, GAME_REGION[1] + 222),
                           NORI:    (GAME_REGION[0] + 496, GAME_REGION[1] + 281),
                           ROE:     (GAME_REGION[0] + 578, GAME_REGION[1] + 281),
                           SALMON:  (GAME_REGION[0] + 496, GAME_REGION[1] + 329),}
    RICE1_COORDS = (GAME_REGION[0] + 543, GAME_REGION[1] + 294)
    RICE2_COORDS = (GAME_REGION[0] + 545, GAME_REGION[1] + 269)

    NORMAL_DELIVERY_BUTTON_COORDS = (GAME_REGION[0] + 495, GAME_REGION[1] + 293)

    MAT_COORDS = (GAME_REGION[0] + 190, GAME_REGION[1] + 375)

    LEVEL = 1


#pyautogui.locateOnScreen()
