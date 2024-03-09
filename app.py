
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
#from commands.start_command import start
import fastf1
def returnBot():
    token = "***REMOVED***"
    return telebot.TeleBot(token)

coda_comandi = []

bot = returnBot()
print("Bot on.")
bot.send_message(1694709046, "bot on")
def chiudi_messaggio(messaggio):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Chiudi", callback_data="cb_yes"),
                               InlineKeyboardButton("No", callback_data="cb_no"))
    return markup
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Questo bot ha lo scopo di mandare i tempi sul giro di tutte le sessioni di F1 di uno specifico pilota.\nI tempi sul giro diventeranno disponibili dopo circa 1 ora-1 ora e mezza dalla fine della sessione.\nDigita /help per avere maggiore informazioni sui comandi\nQuesto bot è stato creato da @andreanxx")

@bot.message_handler(commands=["help"])
def help(message):
    lista_comandi = "LISTA DEI COMANDI:\n/sessione [anno] [circuito] [tipo_sessione] [pilota] - Questo comando ti darà i tempi sul giro di un pilota a tua scelta. Per utilizzarlo dovrai inserire l'anno della sessione, il nome del circuito, il tipo di sessione e il pilota.\nI tipi di sessione che puoi inserire: 'R' (gara), 'Q' (qualifica), 'SQ' (qualifica sprint), 'FP1' (prova lib.1), 'FP2' (prova lib.2), 'FP3' (prova lib.3)\nI nomi dei piloti dovranno essere inseriti con il loro cognome abbreviato di 3 caratteri (Es: LEC,VER,ALO,SAI,NOR). Se non te li ricordi, puoi ottenere una lista dei nomi dei piloti abbreviati con il comando /nomi_piloti.\nES UTILIZZO DEL COMANDO /sessione:\n/sessione 2024 Bahrain R LEC"
    bot.send_message(message.chat.id, lista_comandi)
@bot.message_handler(commands=["nomi_piloti"])
def nomi_piloti(message):
    lista_piloti = """
ALB	Alexander Albon
ALO	Fernando Alonso
BEA	Oliver Bearman
BOT	Valtteri Bottas
DEV	Nyck de Vries
GAS	Pierre Gasly
HAM	Lewis Hamilton
HUL	Nico Hülkenberg
LAT	Nicholas Latifi
LAW	Liam Lawson
LEC	Charles Leclerc
MAG	Kevin Magnussen
NOR	Lando Norris
OCO	Esteban Ocon
PER	Sergio Pérez
PIA	Oscar Piastri
RIC	Daniel Ricciardo
RUS	George Russell
SAI	Carlos Sainz Jr.
SAR	Logan Sargeant
SCH [a]	Mick Schumacher
STR	Lance Stroll
TSU	Yuki Tsunoda
VER	Max Verstappen
ZHO	Zhou Guanyu
VER Max Verstappen
                        """
    bot.reply_to(message,"LISTA PILOTI:\n"+lista_piloti)
@bot.message_handler(commands=["sessione"])
def get_sessione(message):
    args = message.text.split()
    anno = int(args[1])
    track = args[2]
    tipo = args[3]
    pilota = args[4]
    if len(pilota) != 3:
        bot.reply_to(message, "Pilota non valido, ricorda di mandare il pilota nella formattazione a 3 caratteri, es: LEC,ALO,VER,SAI")
    else:
        posizione_in_coda = bot.reply_to(message, f"Sessione n.{len(coda_comandi)+1} aggiunta alla coda")
        coda_comandi.append([anno,track,tipo,pilota,message, posizione_in_coda])
        #attendi_messaggio = bot.reply_to(message, "Carico la sessione...")
        #race = fastf1.get_session(anno,track,tipo)
        #race.load()
        #bot.delete_message(message.chat.id, attendi_messaggio.message_id)
        #laps = race.laps.pick_driver(pilota.upper()).reset_index()
        #lap_times = [str(index) + ". " +str(lap) for index,lap in enumerate(laps['LapTime'])]
        #testo = f"TEMPI DI {pilota} in {track} {anno} nella {tipo}:\n" + "\n".join(lap_times).replace("0 days 00:", "")
        #if(len(lap_times) > 0):
        #    markup = InlineKeyboardMarkup(row_width=1)
        #    chiudi = InlineKeyboardButton('Chiudi', callback_data='chiusura')
        #    markup.add(chiudi)
        #    bot.reply_to(message, testo, reply_markup = markup)
        #else:
        #    bot.reply_to(message, "Errore: Sessione non disponibile!\nRicontrolla i parametri che mi hai fornito o attendi che i dati verranno caricati")
@bot.callback_query_handler(func=lambda call:True)
def chiusura(callback):
    if callback.message:
        if callback.data == 'chiusura':
            bot.delete_message(callback.message.chat.id,callback.message.id)
def register_handlers():
    #bot.register_message_handler(start, commands=['start'])
    pass
    

#register_handlers()

def main():        
    bot.polling(non_stop=True)
def commandqueue():
    while 1:
        for comando in coda_comandi:
            message = comando[4]
            anno = comando[0]
            # track,tipo,pilota
            track = comando[1]
            tipo = comando[2]
            pilota = comando[3]

            attendi_messaggio = bot.edit_message_text(chat_id=comando[5].chat.id, message_id=comando[5].message_id, text="Carico la sessione...")
            race = fastf1.get_session(anno,track,tipo)
            race.load()
            bot.delete_message(message.chat.id, attendi_messaggio.message_id)
            laps = race.laps.pick_driver(pilota.upper()).reset_index()
            lap_times = [str(lap) for lap in laps['LapTime']]
            compounds = [str(i) + ". " + str(compound) for i,compound in enumerate(laps['Compound'])]
            testo =f"TEMPI DI {pilota} in {track} {anno} nella {tipo}:\n"
            for i in range(len(lap_times)):
                testo+="".join(compounds[i]) + " " + "".join(lap_times[i]).replace("0 days 00:", "") + "\n"
            if(len(lap_times) > 0):
                try:
                    markup = InlineKeyboardMarkup(row_width=1)
                    chiudi = InlineKeyboardButton('Chiudi', callback_data='chiusura')
                    markup.add(chiudi)
                    bot.reply_to(message, testo, reply_markup = markup)
                    coda_comandi.remove(comando)
                except:
                    bot.reply_to(message, "I dati di questa sessione non sono ancora accessibili.")
            else:
                bot.reply_to(message, "Errore: Sessione non disponibile!\nRicontrolla i parametri che mi hai fornito o attendi che i dati verranno caricati")

if __name__ == '__main__':
    threading.Thread(target=main).start()
    threading.Thread(target=commandqueue).start()
