import MetaTrader5 as mt5


def initialize_mt5():
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return None
    return mt5


def login_mt5(account, server, password):
    authorized = mt5.login(account, server=server, password=password)
    if authorized:
        return True
    else:
        print("failed to connect at account #{}, error code: {}".format(account, mt5.last_error()))
        return False


def shutdown_mt5():
    mt5.shutdown()


def connect(account, server, password):
    mt5_instance = initialize_mt5()
    if mt5_instance:
        connected = login_mt5(account, server, password)
        if connected:
            return True
        else:
            shutdown_mt5()
    return False
