# coding=utf-8

import sys
import json
import time
import getopt
import datetime
import traceback

import okex.spot_api as spot
import okex.swap_api as swap
import okex.futures_api as future
import okex.account_api as account


class Strategy(object):
    def __init__(self, config_filename):
        # 加载配置文件
        self._config_filename = config_filename

        self.equitySum = 0
        self.currencyList = [
            {
                "currency": "BTC",
                "instrument_id": "",
                "equity": 0,
                "gain": 0,
                "insurance": 0,
                "long": 0,
                "short": 0,
                "grid_long": 0,
                "grid_short": 0,
                "baseline": 0,
                "changed": 0,
                "best": 0,
                "grid_order": None
            },
            {
                "currency": "LTC",
                "instrument_id": "",
                "equity": 0,
                "gain": 0,
                "insurance": 0,
                "long": 0,
                "short": 0,
                "grid_long": 0,
                "grid_short": 0,
                "baseline": 0,
                "changed": 0,
                "best": 0,
                "grid_order": None
            },
            {
                "currency": "ETH",
                "instrument_id": "",
                "equity": 0,
                "gain": 0,
                "insurance": 0,
                "long": 0,
                "short": 0,
                "grid_long": 0,
                "grid_short": 0,
                "baseline": 0,
                "changed": 0,
                "best": 0,
                "grid_order": None
            },
            {
                "currency": "EOS",
                "instrument_id": "",
                "equity": 0,
                "gain": 0,
                "insurance": 0,
                "long": 0,
                "short": 0,
                "grid_long": 0,
                "grid_short": 0,
                "baseline": 0,
                "changed": 0,
                "best": 0,
                "grid_order": None
            },
            {
                "currency": "BCH",
                "instrument_id": "",
                "equity": 0,
                "gain": 0,
                "insurance": 0,
                "long": 0,
                "short": 0,
                "grid_long": 0,
                "grid_short": 0,
                "baseline": 0,
                "changed": 0,
                "best": 0,
                "grid_order": None
            },
            {
                "currency": "XRP",
                "instrument_id": "",
                "equity": 0,
                "gain": 0,
                "insurance": 0,
                "long": 0,
                "short": 0,
                "grid_long": 0,
                "grid_short": 0,
                "baseline": 0,
                "changed": 0,
                "best": 0,
                "grid_order": None
            }]
        self.currentLong = [{
            "currency": "",
            "instrument_id": "",
            "equity": 0,
            "gain": 0,
            "insurance": 0,
            "long": 0,
            "short": 0
        },
            {
                "currency": "",
                "instrument_id": "",
                "equity": 0,
                "gain": 0,
                "insurance": 0,
                "long": 0,
                "short": 0
        }]
        self.currentShort = [{
            "currency": "",
            "instrument_id": "",
            "equity": 0,
            "gain": 0,
            "insurance": 0,
            "long": 0,
            "short": 0
        },
            {
                "currency": "",
                "instrument_id": "",
                "equity": 0,
                "gain": 0,
                "insurance": 0,
                "long": 0,
                "short": 0
        }]

    def get_config(self):
        with open("./" + self._config_filename, 'r') as load_f:
            return json.load(load_f)

    def update_config(self):
        config_json = self.get_config()

        # 初始化 API 接口
        self._account_api = account.AccountAPI(
            config_json["auth"]["api_key"], config_json["auth"]["seceret_key"], config_json["auth"]["passphrase"], True)
        self._spot_api = spot.SpotAPI(
            config_json["auth"]["api_key"], config_json["auth"]["seceret_key"], config_json["auth"]["passphrase"], True)
        self._future_api = future.FutureAPI(
            config_json["auth"]["api_key"], config_json["auth"]["seceret_key"], config_json["auth"]["passphrase"], True)
        self._swap_api = swap.SwapAPI(
            config_json["auth"]["api_key"], config_json["auth"]["seceret_key"], config_json["auth"]["passphrase"], True)

        # 初始化参数
        self._strategy_id = config_json["strategy_id"]
        self._k_line_period = config_json["k_line_period"]
        self._sampling_num = config_json["sampling_num"]
        self._leverage = config_json["leverage"]
        self._coin_usdt = config_json["coin_usdt"]
        self._coin_usdt_overflow = config_json["coin_usdt_overflow"]
        self._insurance = config_json["insurance"]
        self._long = config_json["long"]
        self._short = config_json["short"]
        self._grid = config_json["grid"]

        # 计算参数
        self._sampling_sum = (self._sampling_num *
                              (1 + self._sampling_num)) / 2

    def get_bar_time(self):
        timestamp = self._future_api.get_kline(
            self.currencyList[0]["instrument_id"], 14400)[0][0]
        return timestamp

    def get_all_instuments_id(self):
        all_instuments_id = self._future_api.get_products()
        for currency in self.currencyList:
            for instument_id in all_instuments_id:
                if(instument_id["alias"] == "quarter" and instument_id["underlying_index"] == currency["currency"]):
                    currency["instrument_id"] = instument_id["instrument_id"]
                    break

    def get_all_position(self):
        long_index = 0
        for currency in self.currencyList:
            position = self._future_api.get_specific_position(
                currency["instrument_id"])
            if(position["holding"]):
                if(currency["grid_long"] > 0):
                    currency["long"] = int(
                        position["holding"][0]["long_qty"]) - currency["grid_long"]
                else:
                    currency["long"] = int(
                        position["holding"][0]["long_qty"]) + currency["grid_long"]
                if(currency["long"] > 0):
                    if(long_index < 2):
                        self.currentLong[long_index] = currency
                    long_index += 1

        short_index = 0
        for currency in self.currencyList:
            position = self._future_api.get_specific_position(
                currency["instrument_id"])
            if(position["holding"]):
                if(currency["grid_short"] > 0):
                    currency["short"] = int(
                        position["holding"][0]["short_qty"]) - currency["grid_short"]
                else:
                    currency["short"] = int(
                        position["holding"][0]["short_qty"]) + currency["grid_short"]
                if(currency["currency"] == "BTC"):
                    if(currency["short"] > self._short["btc_instrument_amount"]):
                        currency["insurance"] = self._insurance["btc_insurance_amount"]
                        currency["short"] = self._short["btc_instrument_amount"]
                        if(short_index < 2):
                            self.currentShort[short_index] = currency
                        short_index += 1
                    elif(currency["short"] == self._short["btc_instrument_amount"]):
                        currency["insurance"] = 0
                        currency["short"] = self._short["btc_instrument_amount"]
                        if(short_index < 2):
                            self.currentShort[short_index] = currency
                        short_index += 1
                    elif(currency["short"] == self._insurance["btc_insurance_amount"]):
                        currency["insurance"] = self._insurance["btc_insurance_amount"]
                        currency["short"] = 0
                    elif(currency["short"] > 0):
                        currency["insurance"] = 0
                        if(short_index < 2):
                            self.currentShort[short_index] = currency
                        short_index += 1
                    else:
                        currency["insurance"] = 0
                        currency["short"] = 0
                else:
                    if(currency["short"] > self._short["other_instrument_amount"]):
                        currency["insurance"] = self._insurance["other_insurance_amount"]
                        currency["short"] = self._short["other_instrument_amount"]
                        if(short_index < 2):
                            self.currentShort[short_index] = currency
                        short_index += 1
                    elif(currency["short"] == self._short["other_instrument_amount"]):
                        currency["insurance"] = 0
                        currency["short"] = self._short["other_instrument_amount"]
                        if(short_index < 2):
                            self.currentShort[short_index] = currency
                        short_index += 1
                    elif(currency["short"] == self._insurance["other_insurance_amount"]):
                        currency["insurance"] = self._insurance["other_insurance_amount"]
                        currency["short"] = 0
                    elif(currency["short"] > 0):
                        currency["insurance"] = 0
                        if(short_index < 2):
                            self.currentShort[short_index] = currency
                        short_index += 1
                    else:
                        currency["insurance"] = 0
                        currency["short"] = 0

        self.currentLong = sorted(
            self.currentLong, key=lambda e: e.__getitem__("gain"), reverse=True)
        self.currentShort = sorted(
            self.currentShort, key=lambda e: e.__getitem__("gain"))

    def get_all_equity(self):
        self.equitySum = 0
        for currency in self.currencyList:
            close = self._spot_api.get_kline(
                currency["currency"] + "-USDT", "", "", self._k_line_period)[0][4]
            equity = self._future_api.get_coin_account(
                currency["currency"])["equity"]
            currency["equity"] = float(close) * float(equity)
            self.equitySum += currency["equity"]
        spotAccountInfo = self._spot_api.get_account_info()
        for currency in spotAccountInfo:
            if(currency["currency"] == "USDT"):
                self.equitySum += float(currency["balance"])
                break

    def get_all_gain(self):
        for currency in self.currencyList:
            _k_line_datas = self._future_api.get_kline(
                currency["instrument_id"], self._k_line_period)
            grandGain = [0] * 7
            weightedGain = 0
            for index, data in enumerate(_k_line_datas[0:self._sampling_num]):
                grandGain[index] = (float(data[4]) / float(data[1]) - 1) * 100
                if(index > 0):
                    grandGain[index] = grandGain[index] + grandGain[index - 1]
                    weightedGain += grandGain[index] * (index + 1)
            currency["gain"] = weightedGain / self._sampling_sum

    def init_insurance(self):
        for currency in self.currencyList:
            if(currency["insurance"] == 0):
                currency_to_insurance_result = {}
                if(currency["currency"] == "BTC"):
                    currency_to_insurance_result = self._future_api.take_order(
                        "", currency["instrument_id"], 2, 0, self._insurance["btc_insurance_amount"], 1, self._leverage)
                    if(currency_to_insurance_result["result"]):
                        currency["insurance"] = self._insurance["btc_insurance_amount"]
                else:
                    currency_to_insurance_result = self._future_api.take_order(
                        "", currency["instrument_id"], 2, 0, self._insurance["other_insurance_amount"], 1, self._leverage)
                    if(currency_to_insurance_result["result"]):
                        currency["insurance"] = self._insurance["other_insurance_amount"]

    def update_insurance(self):
        for currency in self.currencyList:
            if(currency["insurance"] != 0 and currency["gain"] > 0):
                self._future_api.take_order(
                    "", currency["instrument_id"], 4, 0, currency["insurance"], 1, self._leverage)
                currency["changed"] = 1
                currency["insurance"] = 0
            if(currency["insurance"] == 0 and currency["gain"] < 0):
                if(currency["currency"] == "BTC"):
                    self._future_api.take_order(
                        "", currency["instrument_id"], 2, 0, self._insurance["btc_insurance_amount"], 1, self._leverage)
                    currency["insurance"] = self._insurance["btc_insurance_amount"]
                    currency["changed"] = 1
                else:
                    self._future_api.take_order(
                        "", currency["instrument_id"], 2, 0, self._insurance["other_insurance_amount"], 1, self._leverage)
                    currency["insurance"] = self._insurance["other_insurance_amount"]
                    currency["changed"] = 1

            currency_future_amount = self._future_api.get_coin_account(
                currency["currency"])
            overflow_amount = float(
                currency_future_amount["equity"]) - self._insurance["usdt_insurance_amount"] / float(self._spot_api.get_kline(
                    currency["currency"] + "-USDT", "", "", self._k_line_period)[0][4])
            print(currency["currency"] + " " + str(abs(overflow_amount)) +
                  " " + str(currency_future_amount["total_avail_balance"]))
            if(overflow_amount > 0 and abs(overflow_amount) > float(currency_future_amount["total_avail_balance"])):
                print("Skip")
                continue
            if(overflow_amount > 0):
                transfer_result = self._account_api.coin_transfer(
                    currency["currency"], overflow_amount, 3, 1)
                if(transfer_result["result"]):
                    time.sleep(10)
                    self._spot_api.take_order(
                        "market", "sell", currency["currency"] + "-USDT", overflow_amount, 0)
            elif(overflow_amount < 0):
                original_amount = float(self._spot_api.get_coin_account_info(
                    currency["currency"])["balance"])
                usdt_amount = (-overflow_amount) * float(self._spot_api.get_kline(
                    currency["currency"] + "-USDT", "", "", self._k_line_period)[0][4])
                usdt_to_currency_result = self._spot_api.take_order(
                    "market", "buy", currency["currency"] + "-USDT", 0, usdt_amount)
                if(usdt_to_currency_result["result"]):
                    time.sleep(10)
                    transfer_amount = float(self._spot_api.get_coin_account_info(
                        currency["currency"])["balance"]) - original_amount
                    transfer_result = self._account_api.coin_transfer(
                        currency["currency"], transfer_amount, 1, 3)

    def open_long_order(self):
        self.currencyList = sorted(
            self.currencyList, key=lambda e: e.__getitem__("gain"), reverse=True)
        for i in range(0, 2):
            if(self.currencyList[i]["gain"] > 0 and (self.currencyList[i]["currency"] != self.currentLong[0]["currency"] and self.currencyList[i]["currency"] != self.currentLong[1]["currency"])):
                print("当前操作于 " + self.currencyList[i]["currency"])
                if(self.currentLong[i]["currency"]):
                    self._future_api.take_order(
                        "", self.currentLong[i]["instrument_id"], 3, 0, self.currentLong[i]["long"], 1, self._leverage)
                    self.set_changed(self.currentLong[i]["currency"])
                    self.set_best(self.currentLong[i]["currency"], 0)
                order_result = {}
                if(self.currencyList[i]["currency"] == "BTC"):
                    order_result = self._future_api.take_order(
                        "", self.currencyList[i]["instrument_id"], 1, 0, self._long["btc_instrument_amount"], 1, self._leverage)
                    self.set_changed(self.currencyList[i]["currency"])
                    self.set_best(self.currencyList[i]["currency"], 1)
                else:
                    order_result = self._future_api.take_order(
                        "", self.currencyList[i]["instrument_id"], 1, 0, self._long["other_instrument_amount"], 1, self._leverage)
                    self.set_changed(self.currencyList[i]["currency"])
                    self.set_best(self.currencyList[i]["currency"], 1)
                if(order_result["result"]):
                    self.currentLong[i] = self.currencyList[i]
            if(self.currencyList[i]["gain"] < 0 and (self.currencyList[i]["currency"] == self.currentLong[0]["currency"] or self.currencyList[i]["currency"] == self.currentLong[1]["currency"])):
                print("当前操作于 " + self.currencyList[i]["currency"])
                close_result = self._future_api.take_order(
                    "", self.currencyList[i]["instrument_id"], 3, 0, self.currentLong[i]["long"], 1, self._leverage)
                self.set_changed(self.currencyList[i]["currency"])
                self.set_best(self.currencyList[i]["currency"], 0)
                if(close_result["result"]):
                    self.currentLong[self.currentLong.index(self.currencyList[i])] = {
                        "currency": "",
                        "instrument_id": "",
                        "equity": 0,
                        "gain": 0,
                        "insurance": 0,
                        "long": 0,
                        "short": 0
                    }

    def open_short_order(self):
        self.currencyList = sorted(
            self.currencyList, key=lambda e: e.__getitem__("gain"))
        for i in range(0, 2):
            if(self.currencyList[i]["gain"] < 0 and (self.currencyList[i]["currency"] != self.currentShort[0]["currency"] and self.currencyList[i]["currency"] != self.currentShort[1]["currency"])):
                print("当前操作于 " + self.currencyList[i]["currency"])
                if(self.currentShort[i]["currency"]):
                    self._future_api.take_order(
                        "", self.currentShort[i]["instrument_id"], 4, 0, self.currentShort[i]["short"], 1, self._leverage)
                    self.set_changed(self.currentShort[i]["currency"])
                    self.set_best(self.currentShort[i]["currency"], 0)
                order_result = {}
                if(self.currencyList[i]["currency"] == "BTC"):
                    order_result = self._future_api.take_order(
                        "", self.currencyList[i]["instrument_id"], 2, 0, self._short["btc_instrument_amount"], 1, self._leverage)
                    self.set_changed(self.currencyList[i]["currency"])
                    self.set_best(self.currencyList[i]["currency"], 1)
                else:
                    order_result = self._future_api.take_order(
                        "", self.currencyList[i]["instrument_id"], 2, 0, self._short["other_instrument_amount"], 1, self._leverage)
                    self.set_changed(self.currencyList[i]["currency"])
                    self.set_best(self.currencyList[i]["currency"], 1)
                if(order_result["result"]):
                    self.currentShort[i] = self.currencyList[i]
            if(self.currencyList[i]["gain"] > 0 and (self.currencyList[i]["currency"] == self.currentShort[0]["currency"] or self.currencyList[i]["currency"] == self.currentShort[1]["currency"])):
                close_result = self._future_api.take_order(
                    "", self.currencyList[i]["instrument_id"], 4, 0, self.currentShort[i]["short"], 1, self._leverage)
                self.set_changed(self.currencyList[i]["currency"])
                self.set_best(self.currencyList[i]["currency"], 0)
                if(close_result["result"]):
                    self.currentShort[self.currentShort.index(self.currencyList[i])] = {
                        "currency": "",
                        "instrument_id": "",
                        "equity": 0,
                        "gain": 0,
                        "insurance": 0,
                        "long": 0,
                        "short": 0
                    }

    def dynamicEquilibrium(self):
        try:
            print("[动态平衡中]")
            self.update_config()
            for currency in self.currencyList:
                currency_account = self._spot_api.get_coin_account_info(
                    currency["currency"])
                k_line_data = float(self._spot_api.get_kline(
                    currency["currency"] + "-USDT", "", "", self._k_line_period)[0][4])
                overflow_amount = float(
                    currency_account["balance"]) * k_line_data - self._coin_usdt
                if(overflow_amount * 100 / self._coin_usdt > self._coin_usdt_overflow):
                    result = self._spot_api.take_order(
                        "market", "sell", currency["currency"] + "-USDT", overflow_amount/k_line_data, 0)
                elif(overflow_amount * 100 / self._coin_usdt < -self._coin_usdt_overflow):
                    result = self._spot_api.take_order(
                        "market", "buy", currency["currency"] + "-USDT", "", -overflow_amount)
        except Exception as e:
            print("[动态平衡错误信息]")
            traceback.print_exc()

    # 网格算法
    def set_changed(self, name):
        for currency in self.currencyList:
            if(currency["currency"] == name):
                currency["changed"] = 1
                break

    def set_best(self, name, whether):
        for currency in self.currencyList:
            if(currency["currency"] == name):
                currency["best"] = whether
                break

    def get_baseline(self, instrument_id):
        _k_line_datas = self._future_api.get_kline(
            instrument_id, self._k_line_period)
        return float(_k_line_datas[0][4])

    def get_all_baseline(self):
        for currency in self.currencyList:
            if(currency["currency"] == "BTC"):
                continue
            _k_line_datas = self._future_api.get_kline(
                currency["instrument_id"], self._k_line_period)
            currency["baseline"] = float(_k_line_datas[0][4])

    def reset_grid(self):
        for currency in self.currencyList:
            if(currency["currency"] == "BTC"):
                continue
            if(currency["changed"] == 1):
                currency["baseline"] = self.get_baseline(
                    currency["instrument_id"])
                all_orders = self._future_api.get_order_list(
                    "6", currency["instrument_id"], "", "", "")
                for order in all_orders["order_info"]:
                    if(order["client_oid"]):
                        self._future_api.revoke_order(
                            currency["instrument_id"], "", order["client_oid"])
                if(currency["grid_long"] > 0):
                    self._future_api.take_order(
                        "", currency["instrument_id"], 3, 0, currency["grid_long"], 1, self._leverage)
                if(currency["grid_short"] > 0):
                    self._future_api.take_order(
                        "", currency["instrument_id"], 4, 0, currency["grid_short"], 1, self._leverage)
                currency["grid_long"] = 0
                currency["grid_short"] = 0
                currency["grid_order"] = None
                if(not currency["best"]):
                    continue
                if(not currency["grid_order"]):
                    currency["grid_order"] = [None for n in range(
                        self._grid["max_grid_distence"] * 2)]
                for order_num, order in enumerate(currency["grid_order"]):
                    if(not order):
                        if(currency["gain"] > 0):
                            if(order_num < 5):
                                order_id = "OL" + \
                                    str(order_num+1) + currency["currency"]
                                order_price = currency["baseline"] * (
                                    1 - self._grid["grid_distence"] * (order_num + 1) * 0.01)
                                order_result = self._future_api.take_order(
                                    order_id, currency["instrument_id"], 1, order_price, self._grid["instrument_amount"], 0, self._leverage)
                                print(order_result)
                                if(order_result["result"]):
                                    currency["grid_order"][order_num] = order_id
                            else:
                                order_id = "CL" + \
                                    str(order_num-5+1) + currency["currency"]
                                order_price = currency["baseline"] * (
                                    1 + self._grid["grid_distence"] * (order_num-5+1) * 0.01)
                                order_result = self._future_api.take_order(
                                    order_id, currency["instrument_id"], 3, order_price, self._grid["instrument_amount"], 0, self._leverage)
                                print(order_result)
                                if(order_result["result"]):
                                    currency["grid_order"][order_num] = order_id
                        else:
                            if(order_num < 5):
                                order_id = "OS" + \
                                    str(order_num+1) + currency["currency"]
                                order_price = currency["baseline"] * (
                                    1 + self._grid["grid_distence"] * (order_num + 1) * 0.01)
                                order_result = self._future_api.take_order(
                                    order_id, currency["instrument_id"], 2, order_price, self._grid["instrument_amount"], 0, self._leverage)
                                print(order_result)
                                if(order_result["result"]):
                                    currency["grid_order"][order_num] = order_id
                            else:
                                order_id = "CS" + \
                                    str(order_num - 5 + 1) + \
                                    currency["currency"]
                                order_price = currency["baseline"] * (
                                    1 - self._grid["grid_distence"] * (order_num-5+1) * 0.01)
                                order_result = self._future_api.take_order(
                                    order_id, currency["instrument_id"], 4, order_price, self._grid["instrument_amount"], 0, self._leverage)
                                print(order_result)
                                if(order_result["result"]):
                                    currency["grid_order"][order_num] = order_id
                    currency["changed"] = 0

    def check_orders(self):
        for currency in self.currencyList:
            if(currency["currency"] == "BTC"):
                continue
            if(not currency["best"]):
                continue
            for order_num, order in enumerate(currency["grid_order"]):
                if(order):
                    order_info = self._future_api.get_order_info(
                        currency["instrument_id"], "", order)
                    if(order[:2] == "OL" and order_info["order_type"] == "2"):
                        currency["grid_long"] += self._grid["instrument_amount"]
                        order_id = "CL" + \
                            order[2] + currency["currency"]
                        order_price = order_info["price"] * \
                            (1 + self._grid["grid_distence"] * 0.01)
                        order_result = self._future_api.take_order(
                            order_id, currency["instrument_id"], 3, order_price, self._grid["instrument_amount"], 0, self._leverage)
                        print(order_result)
                        if(order_result["result"]):
                            currency["grid_order"][order_num] = order_id
                    elif(order[:2] == "OS" and order_info["order_type"] == "2"):
                        currency["grid_short"] += self._grid["instrument_amount"]
                        order_id = "CS" + \
                            order[2] + currency["currency"]
                        order_price = order_info["price"] * \
                            (1 - self._grid["grid_distence"] * 0.01)
                        order_result = self._future_api.take_order(
                            order_id, currency["instrument_id"], 4, order_price, self._grid["instrument_amount"], 0, self._leverage)
                        print(order_result)
                        if(order_result["result"]):
                            currency["grid_order"][order_num] = order_id
                    elif(order[:2] == "CL" and order_info["order_type"] == "2"):
                        currency["grid_long"] -= self._grid["instrument_amount"]
                        order_id = "OL" + \
                            order[2] + currency["currency"]
                        order_price = order_info["price"] * \
                            (1 - self._grid["grid_distence"] * 0.01)
                        order_result = self._future_api.take_order(
                            order_id, currency["instrument_id"], 1, order_price, self._grid["instrument_amount"], 0, self._leverage)
                        print(order_result)
                        if(order_result["result"]):
                            currency["grid_order"][order_num] = order_id
                    elif(order[:2] == "CS" and order_info["order_type"] == "2"):
                        currency["grid_short"] -= self._grid["instrument_amount"]
                        order_id = "OS" + \
                            order[2] + currency["currency"]
                        order_price = order_info["price"] * \
                            (1 + self._grid["grid_distence"] * 0.01)
                        order_result = self._future_api.take_order(
                            order_id, currency["instrument_id"], 2, order_price, self._grid["instrument_amount"], 0, self._leverage)
                        print(order_result)
                        if(order_result["result"]):
                            currency["grid_order"][order_num] = order_id
    
    def init(self):
        self.update_config()
        self.get_all_instuments_id()
        # 输出当前参数信息
        # print("BTC 开多: %d    其他开多: %d" % (
        #     self._long["btc_instrument_amount"], self._long["other_instrument_amount"]))
        # print("BTC 开空: %d    其他开空: %d" % (
        #     self._short["btc_instrument_amount"], self._short["other_instrument_amount"]))
        # print("周期: %d    采样个数: %d    杠杆: %d" % (
        #     self._k_line_period, self._sampling_num, self._leverage))

    def start_grid(self):
        try:
            print("[动态网格模块检测]")
            self.reset_grid()
            self.check_orders()
            print("[当前网格信息]")
            self.get_all_position()
            for currency in self.currencyList:
                print(currency)
            print("\n")
        except Exception as e:
            print("[错误信息]")
            traceback.print_exc()
            print("[当前网格信息]")
            self.get_all_position()
            for currency in self.currencyList:
                print(currency)
            print("\n")

    def start(self):
        try:
            print(datetime.datetime.now())
            self.get_all_gain()
            print("[更新套保中]")
            self.get_all_position()
            time.sleep(3)
            self.update_insurance()
            # self.init_insurance()
            print("[更新持仓信息中]")
            self.get_all_position()
            print("[开始运行策略 %d]" % self._strategy_id)
            time.sleep(10)
            self.open_long_order()
            time.sleep(10)
            self.open_short_order()
            time.sleep(10)
            print("[当前开多]")
            print(self.currentLong)
            print("[当前开空]")
            print(self.currentShort)
            # print("[拉取收益信息]")
            # self.get_all_equity()
            # print("当前净值: " + str(self.equitySum))
            print("[当前数据信息]")
            self.get_all_position()
            for currency in self.currencyList:
                print(currency)
            print("\n")
        except Exception as e:
            print("[错误信息]")
            traceback.print_exc()
            try:
                print("[尝试重新运行策略 %d]" % self._strategy_id)
                self.get_all_position()
                time.sleep(10)
                self.open_long_order()
                time.sleep(10)
                self.open_short_order()
                time.sleep(10)
                print("\n[当前开多]")
                print(self.currentLong)
                print("[当前开空]")
                print(self.currentShort)
                # print("[拉取收益信息]")
                # self.get_all_equity()
                # print("当前净值: " + str(self.equitySum))
                print("[当前数据信息]")
                self.get_all_position()
                for currency in self.currencyList:
                    print(currency)
                print("\n")
            except Exception as e_again:
                print("[错误信息x2]")
                traceback.print_exc()

    def clear(self):
        for currency in self.currencyList:
            all_orders = self._future_api.get_order_list(
                    "6", currency["instrument_id"], "", "", "")
            for order in all_orders["order_info"]:
                if(order["client_oid"]):
                    self._future_api.revoke_order(
                        currency["instrument_id"], "", order["client_oid"])
            position = self._future_api.get_specific_position(
                currency["instrument_id"])
            if(int(position["holding"][0]["long_qty"])):
                self._future_api.take_order(
                    "", currency["instrument_id"], 3, 0, int(position["holding"][0]["long_qty"]), 1, self._leverage)
            if(int(position["holding"][0]["short_qty"])):
                self._future_api.take_order(
                    "", currency["instrument_id"], 4, 0, int(position["holding"][0]["short_qty"]), 1, self._leverage)


if __name__ == '__main__':
    config_filename = "config.json"
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:', ['config='])
        for opt, arg in opts:
            if opt in ("-c", "--config"):
                f = open("./" + arg, "r")
                config_filename = arg
    except (getopt.GetoptError, FileNotFoundError):
        print("命令行参数错误: 获取配置文件失败")
        sys.exit(1)

    strategy = Strategy(config_filename)
    # strategy.dynamicEquilibrium()
    strategy.init()
    strategy.clear()
    strategy.start()
    # strategy.start_grid()
    last_bar_time = strategy.get_bar_time()
    now_bar_time = last_bar_time
    while(True):
        strategy.init()
        # strategy.dynamicEquilibrium()
        # strategy.start_grid()
        now_bar_time = strategy.get_bar_time()
        if(now_bar_time != last_bar_time):
            strategy.start()
        last_bar_time = now_bar_time
        time.sleep(60)
