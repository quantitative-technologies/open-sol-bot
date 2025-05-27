from aiogram.fsm.state import State, StatesGroup


class StartStates(StatesGroup):
    WAITING_FOR_ACTIVATION_CODE = State()


class CopyTradeStates(StatesGroup):
    """Copy trade states"""

    MENU = State()  # Main menu state

    # Copy trade creation states
    CREATING = State()  # Creating copy trade state
    CREATE_WAITING_FOR_ADDRESS = State()  # Waiting for wallet address input during creation
    CREATE_WAITING_FOR_ALIAS = State()  # Waiting for alias input during creation
    CREATE_WAITING_FOR_FIXED_BUY_AMOUNT = State()  # Waiting for fixed buy amount input during creation
    CREATE_WAITING_FOR_PRIORITY = State()  # Waiting for priority fee input during creation
    CREATE_WAITING_FOR_CUSTOM_SLIPPAGE = State()  # Waiting for custom slippage input during creation

    # Copy trade editing states
    EDITING = State()  # Editing copy trade state
    EDIT_WAITING_FOR_ADDRESS = State()  # Waiting for wallet address input during editing
    EDIT_WAITING_FOR_ALIAS = State()  # Waiting for alias input during editing
    EDIT_WAITING_FOR_FIXED_BUY_AMOUNT = State()  # Waiting for fixed buy amount input during editing
    EDIT_WAITING_FOR_PRIORITY = State()  # Waiting for priority fee input during editing
    EDIT_WAITING_FOR_CUSTOM_SLIPPAGE = State()  # Waiting for custom slippage input during editing


class MonitorStates(StatesGroup):
    MENU = State()
    CREATING = State()  # Creating monitor state
    CREATE_WAITING_FOR_ADDRESS = State()  # Waiting for wallet address input during creation
    CREATE_WAITING_FOR_ALIAS = State()  # Waiting for alias input during creation

    EDITING = State()  # Editing monitor state
    EDIT_WAITING_FOR_ALIAS = State()  # Waiting for alias input during editing


class SettingStates(StatesGroup):
    EDIT_QUICK_SLIPPAGE = State()
    WAITING_FOR_QUICK_SLIPPAGE = State()  # Waiting for quick slippage input
    WAITING_FOR_SANDWICH_SLIPPAGE = State()  # Waiting for anti-sandwich slippage input
    WAITING_FOR_BUY_PRIORITY_FEE = State()  # Waiting for buy priority fee input
    WAITING_FOR_SELL_PRIORITY_FEE = State()  # Waiting for sell priority fee input
    WAITING_FOR_CUSTOM_BUY_AMOUNT = State()  # Waiting for custom buy amount input
    WAITING_FOR_CUSTOM_SELL_PCT = State()  # Waiting for custom sell percentage input


class SwapStates(StatesGroup):
    MENU = State()
    WAITING_FOR_TOKEN_MINT = State()
    WAITING_BUY_AMOUNT = State()
    WAITING_SELL_PCT = State()


class WalletStates(StatesGroup):
    MENU = State()
    WAITING_FOR_NEW_PRIVATE_KEY = State()
