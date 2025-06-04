import telebot, asyncio, json, os, pathlib

bot = telebot.TeleBot("")

balance = {}
chat_balance = {}
bets = {}

def init_load(data):
    path_data = os.path.dirname(os.path.abspath(__file__)) + "\\" + data + ".json"
    print(path_data)

    check_file = pathlib.Path(path_data)
    if check_file.exists():
        b_d = {}
        with open(data + ".json", "r") as fopen:
            b_d = json.load(fopen)
        for i in b_d:
            if data == "balance":
                balance[int(i)] = b_d[i]
            elif data == "chat_balance":
                chat_balance[int(i)] = b_d[i]

def save_data_balance():
    with open("balance.json", "w") as fopen:
        json.dump(balance, fopen)
    with open("chat_balance.json", "w") as fopen:
        json.dump(chat_balance, fopen)

def message(id, msg_text, save_id = False):
    if save_id:
        if bets[id]["update_msg"] == 0:
            msg_rs = bot.send_message(id, msg_text)
            bets[id]["update_msg"] = msg_rs.message_id
            return 0
        else:
            bot.edit_message_text(msg_text, id, bets[id]["update_msg"])
        return 0
    bot.send_message(id, msg_text)
    return 0

@bot.message_handler(content_types=['dice'])
def dice_value(msg):
    value = msg.dice.value
    message(msg.chat.id, "Выпало: " + str(value))

async def pull_result(msg):
    await asyncio.sleep(4)
    result_value = msg.dice.value
    bets[msg.chat.id]["is_running"] = False
    res_text = "Победители:\n"
    if msg.chat.id not in chat_balance.keys():
        chat_balance[msg.chat.id] = 0
    for i in bets[msg.chat.id]["bets"]:
        if i not in balance.keys():
            balance[i] = 100000
        res = bets[msg.chat.id]["bets"][i]
        total, total_to_id = percent_coeff(msg)
        win_coeff = (total / (total_to_id[res["point"]] if total_to_id[res["point"]] != 0 else total) if res["point"] == result_value else -1)
        balance[i] += int(res["value"] * win_coeff)
        chat_balance[msg.chat.id] += res["value"]
        if res["point"] == result_value:
            res_text += "%s %s выиграл %d\n" % (res["first_name"], res["last_name"], res["value"] * win_coeff)
            chat_balance[msg.chat.id] -= int(res["value"] * win_coeff)
    if res_text != "Победители:\n":
        message(msg.chat.id, res_text)
    else:
        message(msg.chat.id, "Победителей нет")
    bets[msg.chat.id]["bets"] = {}
    save_data_balance()
    bets[msg.chat.id]["update_msg"] = 0
    message(msg.chat.id, "Принимаем ставки на следующий бросок", True)

def set_bet(msg, point, value):
    if msg.chat.id not in bets.keys():
        bets[msg.chat.id] = {"is_running" : False, "update_msg" : 0, "bets" : {}}
    
    if bets[msg.chat.id]["is_running"]:
        message(msg.chat.id, "Ставки не принимаются")
    
    bets[msg.chat.id]["bets"][msg.from_user.id] = {"point" : point, "value" : value, "first_name" : msg.from_user.first_name, "last_name" : msg.from_user.last_name}
    check_bet(msg)
    #message(msg.chat.id, "Ставка на " + str(point) + " в размере " + str(value) + " выполнена")

def percent_coeff(msg):
    total = 0
    total_to_id = {1 : 0, 2 : 0, 3 : 0, 4 : 0, 5 : 0, 6 : 0}
    for i in bets[msg.chat.id]["bets"]:
        total += bets[msg.chat.id]["bets"][i]["value"]
        total_to_id[bets[msg.chat.id]["bets"][i]["point"]] += bets[msg.chat.id]["bets"][i]["value"]
    return [total, total_to_id]

def check_bet(msg):
    if msg.chat.id not in chat_balance.keys():
            chat_balance[msg.chat.id] = 0
        
    bets_text = "Принятые ставки:\n"
    if msg.chat.id in bets.keys():
        total, total_to_id = percent_coeff(msg)
        for i in bets[msg.chat.id]["bets"]:
            data = bets[msg.chat.id]["bets"][i]
            bets_text += "%s %s: %d (x%0.2f) на %d\n" % (data["first_name"], data["last_name"], data["value"], total / (total_to_id[data["point"]] if total_to_id[data["point"]] != 0 else total), data["point"])
        if bets_text != "Принятые ставки:\n":
            message(msg.chat.id, bets_text + "\n" + "Баланс чата: " + str(chat_balance[msg.chat.id]), True)
        else:
            message(msg.chat.id, "Ставок нет")
    else:
        message(msg.chat.id, "Ставок нет")

@bot.message_handler()
def init_message(msg):
    text_data = msg.text.lower().split(" ")
    if len(text_data) == 3 and text_data[0] == "ставка":
        try:
            point = int(text_data[1])
            value = int(text_data[2])
            if point < 1 or point > 6:
                message(msg.chat.id, "Возможно поставить только на число от 1 до 6")
                return 0
            
            if value > 100000:
                message(msg.chat.id, "Возможно сделать ставку не больше 100к")
                return 0

            if value < 1000:
                message(msg.chat.id, "Возможно сделать ставку не менее 1к")
                return 0

            set_bet(msg, point, value)
            return 0
        except BaseException as e:
            print(e)
            message(msg.chat.id, "Ставка не записана, попробуй еще раз")
            return 0
    if len(text_data) == 1 and text_data[0] == "баланс":
        if msg.from_user.id not in balance.keys():
            balance[msg.from_user.id] = 100000
        
        message(msg.chat.id, "Ваш баланс: " + str(int(balance[msg.from_user.id])))
        return 0
    if len(text_data) == 2 and ((text_data[0] == "баланс" and text_data[1] == "чата") or (text_data[0] == "чат" and text_data[1] == "баланса")):
        if msg.chat.id not in chat_balance.keys():
            chat_balance[msg.chat.id] = 0
        
        message(msg.chat.id, "Баланс чата: " + str(int(chat_balance[msg.chat.id])))
        return 0
    if len(text_data) == 1 and text_data[0] == "ставки":    
        if msg.chat.id not in bets.keys():
            bets[msg.chat.id] = {"is_running" : False, "update_msg" : 0, "bets" : {}}  
        bets[msg.chat.id]["update_msg"] = 0
        check_bet(msg)
        return 0
    
    if len(text_data) == 1 and text_data[0] == "бросить":
        if msg.chat.id not in bets.keys():
            bets[msg.chat.id] = {"is_running" : False, "update_msg" : 0, "bets" : {}}
        
        if bets[msg.chat.id]["is_running"]:
            message(msg.chat.id, "Уже крутим") 
            return 0

        message(msg.chat.id, "Крутим")
        bets[msg.chat.id]["is_running"] = True
        asyncio.run(pull_result(bot.send_dice(msg.chat.id)))
        return 0
    #print(msg)
    #message(msg.chat.id, msg.text + "🖕")

init_load("balance")
init_load("chat_balance")
bot.infinity_polling()

