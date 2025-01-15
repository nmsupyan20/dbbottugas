from telebot import *
from datetime import *
from dotenv import load_dotenv
from koneksi import koneksi
import threading
import time
import pytz
import os

load_dotenv()

token = os.getenv("TOKEN")
bot = TeleBot(token)

@bot.message_handler(commands=['start', 'mulai'])
def perintah_mulai(message):
    pesan_mulai = ("*SELAMAT DATANG DI BOT DAFTAR TUGAS*\n\n"
                   "Berikut ini merupakan daftar perintah dari Tugas Bot\n"
                   "/tambah : Menambah tugas ke daftar.\n"
                   "/daftar : Menampilkan daftar tugas.\n"
                   "/ubah : Mengubah tugas di daftar tugas.\n"
                   "/hapus : Menghapus tugas dari daftar.\n")
    bot.send_message(message.chat.id, pesan_mulai, parse_mode="markdown")

@bot.message_handler(commands=['tambah'])
def perintah_tambah(message):
    chat_id = message.from_user.id
    chat_id = str(chat_id)
    bot.send_message(chat_id, "Silahkan masukkan judul tugas :")
    bot.register_next_step_handler(message, ambil_judul, chat_id)

def ambil_judul(message, chat_id):
    judul = message.text
    judul = judul.capitalize()
    bot.send_message(chat_id, "Silahkan masukkan tanggal dengan format DD/MM/YYYY :")
    bot.register_next_step_handler(message, ambil_tanggal, judul, chat_id)

def ambil_tanggal(message, judul, chat_id):
    try:
        tanggal_str = message.text
        tanggal = datetime.strptime(tanggal_str, "%d/%m/%Y").date()
        hari = tanggal.strftime("%A")

        if hari == "Monday":
            hari = "Senin"
        elif hari == "Tuesday":
            hari = "Selasa"
        elif hari == "Wednesday":
            hari = "Rabu"
        elif hari == "Thursday":
            hari = "Kamis"
        elif hari == "Friday":
            hari = "Jumat"
        elif hari == "Saturday":
            hari = "Sabtu"
        elif hari == "Sunday":
            hari = "Minggu"
        bot.send_message(chat_id, "Silahkan masukkan tenggat waktu dengan format HH:MM :")
        bot.register_next_step_handler(message, proses_perintah_tambah, judul, hari, tanggal, chat_id)
    except Exception:
        bot.send_message(chat_id, "Format tanggal salah, mohon isi sesuai format" )

def proses_perintah_tambah(message, judul, hari, tanggal, chat_id):
    try:
        waktu_str = message.text
        waktu = datetime.strptime(waktu_str, "%H:%M").time()
        waktu_lengkap = datetime.combine(tanggal, waktu)
        pengingat = waktu_lengkap - timedelta(hours=10)
        print(f"Judul {judul} Tanggal {tanggal} hari {hari} waktu {waktu}")
        cn = koneksi()
        cursor = cn.cursor()
        query = "select * from tugas where userId = %s and judul = %s and hari = %s and tanggal = %s and waktu = %s"
        nilai = (chat_id, judul, hari, tanggal, waktu)
        cursor.execute(query, nilai)
        daftar_tugas = cursor.fetchall()
        print(daftar_tugas)
        if len(daftar_tugas) != 0:
            bot.send_message(chat_id, "Tugas telah ada di daftar")
        else:
            query = "insert into tugas (userId, judul, hari, tanggal, waktu, pengingat) values (%s, %s, %s, %s, %s, %s)"
            nilai = (chat_id, judul, hari, tanggal, waktu, pengingat)
            cursor.execute(query, nilai)
            cn.commit()
            pesan_tambah = f"Tugas {judul} dengan tenggat {hari}, {tanggal} - {waktu} telah ditambahkan"
            print("Pesan : ", pesan_tambah)
            bot.send_message(chat_id, pesan_tambah)
    except Exception:
        bot.send_message(chat_id, "Format waktu salah, mohon isi sesuai format")
    finally:
        cursor.close()
        cn.close()

@bot.message_handler(commands=['daftar'])
def perintah_daftar(message):
    cn = koneksi()
    cursor = cn.cursor()
    chat_id = message.from_user.id
    chat_id = str(chat_id)
    query = "delete from tugas where userId = %s and tanggal < curdate()"
    cursor.execute(query, (chat_id,))
    cn.commit()

    query = "select * from tugas where userId = %s order by concat(tanggal, ' ', waktu) asc"
    cursor.execute(query, (chat_id,))
    daftar_tugas = cursor.fetchall()

    if len(daftar_tugas) != 0:
        pesan_daftar = "<b> DAFTAR TUGAS </b>\n\n"
        for i, tugas in enumerate(daftar_tugas):
            id, judul = tugas[0], tugas[2]
            hari, tanggal = tugas[3], tugas[4]
            waktu = tugas[5]
            tanggal_str = datetime.strftime(tanggal, "%d/%m/%Y")
            pesan_daftar += f"{i+1}. {judul} | {hari}, {tanggal_str} - {waktu} ({id})\n"
        bot.send_message(chat_id, pesan_daftar, parse_mode="HTML")
    else:
        bot.send_message(chat_id, "Tidak ada tugas di daftar")
    cursor.close()
    cn.close()

@bot.message_handler(commands=['hapus'])
def perintah_hapus(message):
    cn = koneksi()
    cursor = cn.cursor()
    chat_id = message.from_user.id
    chat_id = str(chat_id)
    query = ("select * from tugas where userId = %s "
             "and tanggal >= curdate() "
             "order by concat(tanggal, ' ', waktu) asc")
    cursor.execute(query, (chat_id,))
    daftar_tugas = cursor.fetchall()
    if len(daftar_tugas) != 0:
        pesan_daftar = "<b> DAFTAR TUGAS </b>\n\n"
        for i, tugas in enumerate(daftar_tugas):
            id, judul = tugas[0], tugas[2]
            hari, tanggal = tugas[3], tugas[4]
            waktu = tugas[5]
            tanggal_str = datetime.strftime(tanggal, "%d/%m/%Y")
            pesan_daftar += f"{i+1}. {judul} | {hari}, {tanggal_str} - {waktu} ({id})\n"
        bot.send_message(chat_id, pesan_daftar, parse_mode="HTML")
        bot.send_message(chat_id, "Tugas dengan id berapa yang ingin anda hapus? ")
        bot.register_next_step_handler(message, ambil_id_hapus, chat_id, cn, cursor)
    else:
        bot.send_message(chat_id, "Tidak ada tugas yang aktif")
        cursor.close()
        cn.close()

def ambil_id_hapus(message, chat_id, cn, cursor):
    id = message.text
    query = "select * from tugas where userId = %s and id = %s"
    nilai = (chat_id, id)
    cursor.execute(query, nilai)
    daftar_tugas = cursor.fetchall()
    if len(daftar_tugas) != 0:
        bot.send_message(chat_id, f"Apakah anda yakin ingin menghapus tugas dengan id {id} (y/n)?")
        bot.register_next_step_handler(message, proses_perintah_hapus, id, chat_id, cn, cursor)
    else:
        bot.send_message(chat_id, f"Tidak ada tugas dengan id {id}")
        cursor.close()
        cn.close()

def proses_perintah_hapus(message, id, chat_id, cn, cursor):
    try:
        if message.text.lower() == "y":
            query = "delete from tugas where userId = %s and id = %s"
            nilai = (chat_id, id)
            cursor.execute(query, nilai)
            cn.commit()
            pesan_hapus = f"Tugas dengan id {id} telah terhapus"
            bot.send_message(chat_id, pesan_hapus)
        elif message.text.lower() == "n":
            bot.send_message(chat_id, "Penghapusan dibatalkan")
    except Exception:
        bot.send_message(chat_id, "Gagal menghapus tugas")
    finally:
        cursor.close()
        cn.close()

@bot.message_handler(commands=['ubah'])
def perintah_ubah(message):
    cn = koneksi()
    cursor = cn.cursor()
    chat_id = message.from_user.id
    chat_id = str(chat_id)
    query = ("select * from tugas where userId = %s "
             "and tanggal >= curdate() "
             "order by concat(tanggal, ' ', waktu) asc")
    cursor.execute(query, (chat_id,))
    daftar_tugas = cursor.fetchall()
    if len(daftar_tugas) != 0:
        pesan_daftar = "<b> DAFTAR TUGAS </b>\n\n"
        for i, tugas in enumerate(daftar_tugas):
            id, judul = tugas[0], tugas[2]
            hari, tanggal = tugas[3], tugas[4]
            waktu = tugas[5]
            tanggal_str = datetime.strftime(tanggal, "%d/%m/%Y")
            pesan_daftar += f"{i+1}. {judul} | {hari}, {tanggal_str} - {waktu} ({id})\n"
        bot.send_message(chat_id, pesan_daftar, parse_mode="HTML")
        bot.send_message(chat_id, "Tugas dengan id berapa yang ingin diubah?")
        bot.register_next_step_handler(message, ambil_id_ubah, chat_id, cn, cursor)
    else:
        bot.send_message(chat_id, "Tidak ada tugas di daftar")
        cursor.close()
        cn.close()

def ambil_id_ubah(message, chat_id, cn, cursor):
    id = message.text
    query = "select * from tugas where userId = %s and id = %s"
    nilai = (chat_id, id)
    cursor.execute(query, nilai)
    daftar = cursor.fetchone()
    if daftar is not None:
        pesan_ambil_ubah = ("Pilih apa yang ingin anda ubah\n"
                        "1. Judul\n"
                        "2. Tanggal\n"
                        "3. Waktu\n"
                        "Jika anda ingin mengubah judul ketik 1 .")
        bot.send_message(chat_id, pesan_ambil_ubah)
        bot.register_next_step_handler(message, proses_perintah_ubah, chat_id, id, cn, cursor, daftar)
    else:
        bot.send_message(chat_id, "Tidak ada tugas dengan id tersebut")
        cursor.close()
        cn.close()

def proses_perintah_ubah(message, chat_id, id, cn, cursor, daftar):
    pilihan = message.text
    if pilihan == "1":
        bot.send_message(chat_id, "Masukkan judul baru : ")
        bot.register_next_step_handler(message, ubah_judul, chat_id, id, cn, cursor)
    elif pilihan == "2":
        bot.send_message(chat_id, "Masukkan tanggal baru dengan format DD/MM/YY :")
        bot.register_next_step_handler(message, ubah_tanggal, chat_id, id, cn, cursor, daftar)
    elif pilihan == "3":
        bot.send_message(chat_id, "Masukkan tenggat waktu baru dengan format HH:MM : ")
        bot.register_next_step_handler(message, ubah_waktu, chat_id, id, cn, cursor, daftar)

def ubah_judul(message, chat_id, id, cn, cursor):
    judul_baru = message.text
    query = "update tugas set judul = %s where userId = %s and id = %s"
    nilai = (judul_baru, chat_id, id)
    cursor.execute(query, nilai)
    cn.commit()
    bot.send_message(chat_id, "Judul telah diubah")
    cursor.close()
    cn.close()

def ubah_tanggal(message, chat_id, id, cn, cursor, daftar):
    try:
        tanggal_baru_str = message.text
        tanggal_baru = datetime.strptime(tanggal_baru_str, "%d/%m/%Y")
        hari_baru = tanggal_baru.strftime("%A")
        if hari_baru == "Monday":
            hari_baru = "Senin"
        elif hari_baru == "Tuesday":
            hari_baru = "Selasa"
        elif hari_baru == "Wednesday":
            hari_baru = "Rabu"
        elif hari_baru == "Thursday":
            hari_baru = "Kamis"
        elif hari_baru == "Friday":
            hari_baru = "Jumat"
        elif hari_baru == "Saturday":
            hari_baru = "Sabtu"
        elif hari_baru == "Sunday":
            hari_baru = "Minggu"
        waktu_baru = str(daftar[5])
        waktu_baru = datetime.strptime(waktu_baru, "%H:%M:%S").time()
        tanggal_lengkap = datetime.combine(tanggal_baru, waktu_baru)
        pengingat_baru = tanggal_lengkap - timedelta(hours=10)
        query = ("update tugas set hari = %s, tanggal = %s, pengingat = %s "
                 "where userId = %s and id = %s")
        nilai = (hari_baru, tanggal_baru, pengingat_baru, chat_id, id)
        cursor.execute(query, nilai)
        cn.commit()
        bot.send_message(chat_id, "Tanggal dan hari telah diubah")
    except Exception as e:
        bot.send_message(chat_id, "Format tanggal salah")
    finally:
        cursor.close()
        cn.close()

def ubah_waktu(message, chat_id, id, cn, cursor, daftar):
    try:
        waktu_baru_str = message.text
        waktu_baru = datetime.strptime(waktu_baru_str, "%H:%M").time()
        tanggal_baru_str = str(daftar[4])
        tanggal_baru = datetime.strptime(tanggal_baru_str, "%Y-%m-%d")
        tanggal_lengkap = datetime.combine(tanggal_baru, waktu_baru)
        pengingat_baru = tanggal_lengkap - timedelta(hours=10)
        query = ("update tugas set waktu = %s, pengingat = %s "
                 "where userId = %s and id = %s")
        nilai = (waktu_baru, pengingat_baru, chat_id, id)
        cursor.execute(query, nilai)
        cn.commit()
        bot.send_message(chat_id, "Waktu telah diubah")
    except Exception as e:
        bot.send_message(chat_id, "Format waktu salah")
    finally:
        cursor.close()
        cn.close()

def kirim_notifikasi():
    cn = koneksi()
    cursor = cn.cursor()
    sekarang = datetime.now().replace(microsecond=0)
    waktu_indonesia = pytz.timezone("Asia/Jakarta")
    atur_waktu = sekarang.astimezone(waktu_indonesia).replace(tzinfo=None)
    print(f"Waktu Indonesia : {atur_waktu}")
    query = ("select * from tugas where pengingat <= %s and notif = FALSE "
             "and concat(tanggal, ' ', waktu) >= %s "
             "order by tanggal, waktu asc")
    cursor.execute(query, (atur_waktu, atur_waktu))
    daftar = cursor.fetchone()
    print(daftar)
    if daftar is not None:
        pesan_notif = f"Tugas {daftar[2]} akan segera berakhir pada {daftar[3]}, {daftar[4]}-{daftar[5]}"
        bot.send_message(daftar[1], pesan_notif)
        query = "update tugas set notif = TRUE where id = %s"
        cursor.execute(query, (daftar[0],))
        cn.commit()
    cursor.close()
    cn.close()

def jalankan_notif():
    while True:
        try:
            kirim_notifikasi()
            time.sleep(180)
        except Exception as e:
            print(f"Error : {e}")

if __name__ == "__main__":
    threading.Thread(target=jalankan_notif, daemon=True).start()
    bot.infinity_polling()
