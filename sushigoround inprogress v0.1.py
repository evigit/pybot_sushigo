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

    
def navigateStartGameMenu():
    '''Performs the clicks to navigate form the start screen to the beginning of the first level'''
    # Click on everything needed to get past the menus at the start of the game.

    # click on Play
    logging.debug('Looking for Play button...')
    while True: # loop because it could be the blue or pink Play button displayed at the moment.
        pos = pyautogui.locateCenterOnScreen(imPath('play_button.png'), region=GAME_REGION)  # pos stands for position
        if pos is not None:
            break
    pyautogui.click(pos, duration=0.25)
    logging.debug('Clicked on Play button.')

    # click on Continue
    pos = pyautogui.locateCenterOnScreen(imPath('continue_button.png'), region=GAME_REGION)
    pyautogui.click(pos, duration=0.25)
    logging.debug('Clicked on Continue button.')

    # click on Skip
    logging.debug('Looking for Skip button...')
    while True:  # loop because it could be the yellow or red Skip button displayed at the moment.
        pos = pyautogui.locateCenterOnScreen(imPath('skip_button.png'), region=GAME_REGION)
        if pos is not None:
            break
    pyautogui.click(pos, duration=0.25)
    logging.debug('Clicked on Skip Button.')

    # click on Continue
    pos = pyautogui.locateCenterOnScreen(imPath('continue_button.png'), region=GAME_REGION)
    pyautogui.click(pos, duration=0.25)
    logging.debug('Clicked on Continue button.')


def startServing():
    """main game playing function. handles all game play: identifying orders, making orders, buying ingredients, etc."""
    global LAST_GAME_OVER_CHECK, INVENTORY, ORDERING_COMPLETE, LEVEL

    # Reset all game state variables.
    oldOrders = {}
    backOrders = {}
    remakeOrders = {}
    remakeItems = {}
    LAST_GAME_OVER_CHECK = time.time()
    ORDERING_COMPLETE = {SHRIMP: None, RICE: None, NORI: None,
                         ROE: None, SALMON: None, UNAGI: None}


# The next part scans the region where customers orders are displayed:

    while True:
        # Check for orders, see which are new and which are gone since last time.
        currentOrders = getOrders()
        added, removed = getOrdersDifference(currentsOrders, oldOrders)
        if added != {}:
            logging.debug('New orders: %s' % (list(added.values())))
            for k in added:
                remakeTimes[k] = time.time() + TIME_TO_REMAKE
        if removed != {}:
            logging.debug('Removed orders: %s' % (list(removed.values())))
            for k in removed:
                del remakeTimes[k]

        #Check if the remake times have past, and add those to the remakeOrders, dictionary.
        for k, remakeTime in copy.copy(remakeTimes).items():
            if time.time() > remakeTime:
                remakeTimes[k] = time.time() + TIME_TO_REMAKE # reset remake time
                remakeOrders[k] = currentsOrders[k]
                logging.debug('%s added to remake orders.' % (currentOrders[k]))

        #Attempt to make the order.
        for pos, order in added.items():
            result = makeOrder(order)
            if result is not None:
                orderIngredient(result)
                backOrders[pos] = order
                logging.debug('Ingredients for %s not available. Putting on back order.' % (order))

        # Clear any finished plates
        if random.randint(1,10) == 1 or time.time() - PLATE_CLEARING_FREQ > LAST_PLATE_CLEARING:
            clickOnPlates()

        # Check if ingredient orders have arrived.
        updateInventory()

        # Go through and see if any back orders can be filled.
        for pos, order in copy.copy(backOrders).items():
            result = makeOrder(order)
            if result is None:
                del backOrders[pos] # remove from back orders
                logging.debug('Filled back order for %s.' % (order))


        if random.randint(1, 5) == 1:
            # order any ingredients that are below the minimum amount
            for ingredient, amount in INVENTORY.items():
                if amount < MIN_INGREDIENTS:
                    orderIngredient(ingredient)


        # check for the "You Win" or "You fail" messages
        if time.time() - 12 > LAST_GAME_OVER_CHECK:
            result = checkForGameover()
            if result == LEVEL_WIN_MESSAGE:
                # player has completed the level

                # Reset inventory and orders.
                INVENTORY = {SHRIMP: 5, RICE: 10,
                             NORI: 10, ROE: 10,
                             SALMON: 5, UNAGI: 5}
                ORDERING_COMPLETE = {SHRIMP: None, RICE: None, NORI: None,
                                     ROE: None, SALMON: None, UNAGI: None}
                backOrders = {}
                remakeOrders = {}
                currentOrders = {}
                oldOrders = {}

                logging.debug('Level %s complete.' % (LEVEL))
                LEVEL += 1
                time.sleep(5) # give another 5 seconds to tally score

                # Click buttons to continue to next level.
                pos = pyautogui.locateCenterOnScreen(imPath('continue_button.png'), region=GAME_REGION)
                pyautogui.click(pos, duration=0.25)
                logging.debug('Clicked on Continue button.')
                pos = pyautogui.locateCenterOnScreen(imPath('continue_button.png'), region=GAME_REGION)

                if LEVEL <= 7: # click the second continue if the game isn't finished.
                    pyautogui.click(pos, duration=0.25)
                    logging.debug('Clicked on Continue button.')

                oldOrders = currentOrders


def clickOnPlates():
    """Clicks the mouse on the six places where finished plates will be flashing. This function does
    not check for flashing plates, but simply clicks on all six places """

    # Sets LAST_PLATE_CLEARING to the current time
    global LAST_PLATE_CLEARING

    # just blindly click on all 6 spot where a plates should be
    for i in range(6):
        pyautogui.click(83 + GAME_REGION[0] + (i * 101), GAME_REGION[1] + 203)
    LAST_PLATE_CLEARING = time.time()


def getOrders():
    """Scans the screen for orders being made. Returns a dictionary with a (left, top, width, height)
    tuple of integers for keys and the order constant for a value."""

    # The order constants are ONIGIRI, GUNKAN_MAKI, CALIFORNIA_ROLL, SALMON_ROLL, SHRIMP_SUSHI, UNAGI_ROLL,
    # DRAGON_ROLL, COMBO.
    orders = {}
    for orderType in (ALL_ORDER_TYPES):
        allOrders = pyautogui.locateAllOnScreen(imPath('%s_oder.png' % orderType), region=(GAME_REGION[0] + 32
                                                                                           GAME_REGION[1] + 46, 558, 44)
        for order in allOrders:
            orders[order] = orderType
        return orders

def getOrdersDifference(newOrders, oldOrders):
    """Finds the differences between the orders dictionaries passed. Return value is a tuple of two dictionaries.
    The first dictionary is the "added" dictionaty of orders newOrders <- oldOrders.
    The second dictionary is the "removed" dictionary of orders in oldOrders but removed in newOrders.
    Each dictionary has (left, top, width, height) for keys and an order constant for a value."""
    added = {}
    removed = {}

    # find all orders in newOrders that are new and not found in oldOrders
    for k in newOrders:
        if k not in oldOrders:
            added[k] = newOrders[k]
    # find all orders in oldOrders that were removed and not found in newOrders
    for k in oldOrders:
        if k not in newOrders:
            removed[k] = oldOrders[k]

    return added, removed
