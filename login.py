from virl2_client import ClientLibrary

# VIRL2 sunucusuna bağlan
def connect_to_virl2():
    client = ClientLibrary("https://192.168.101.137", "admin", "muji123.", ssl_verify=False)
    print("SSL Verification disabled")
    return client

# LAB ismi al ve var olan LAB'ı kontrol et
def get_lab_name(client):
    while True:
        lab_name = input("Lütfen LAB için bir isim girin: ")
        existing_labs = client.find_labs_by_title(lab_name)
        if existing_labs:
            overwrite = input(f"'{lab_name}' isimli bir LAB zaten var. Üzerine yazmak istiyor musunuz? (E/H): ").strip().lower()
            if overwrite == "e":
                # Var olan LAB'ı sil
                for lab in existing_labs:
                    lab.remove()
                print(f"'{lab_name}' isimli LAB silindi ve yeni bir LAB oluşturulacak.")
                break
            else:
                print("Lütfen farklı bir LAB ismi girin.")
        else:
            break
    return lab_name

# Router'ları oluştur ve hostname'lerini ayarla
def create_routers(lab, devices):
    nodes = {}
    x, y = 50, 100  # İlk router'ın başlangıç koordinatları
    horizontal = True  # İlk 3 router horizontal, sonraki 3 router vertical

    for i, device in enumerate(devices):
        # Cihaz ismi küçük harfle başlıyorsa "iol-xe", büyük harfle başlıyorsa "iosv" kullan
        if device.startswith('s'):
            node_definition = "ioll2-xe"
        elif device.startswith('S'):
            node_definition = "iosvl2"
        else:
            node_definition = "iol-xe" if device[0].islower() else "iosv"
        
        node = lab.create_node(device, node_definition, x, y)  # Cihaz ismini orijinal haliyle kullan
        node.config = f"hostname {device}"  # Hostname'i orijinal büyük/küçük harf ile ayarla
        nodes[device] = node
        print(f"{device} router'ı ({x}, {y}) koordinatlarında oluşturuldu ve hostname ayarlandı. (Node Definition: {node_definition})")

        # Koordinatları güncelle
        if horizontal:
            x += 200  # Horizontal yerleşim için x koordinatını artır
            if (i + 1) % 3 == 0:  # Her 3 router'dan sonra vertical yerleşime geç
                horizontal = False
                x -= 600  # x koordinatını başa al
                y += 200  # y koordinatını artır
        else:
            y += 200  # Vertical yerleşim için y koordinatını artır
            if (i + 1) % 6 == 0:  # Her 6 router'dan sonra horizontal yerleşime geç
                horizontal = True
                y -= 600  # y koordinatını başa al
                x += 200  # x koordinatını artır

    return nodes

# Bağlantıları oluştur
def create_connections(lab, nodes, lines):
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 4:  # Satır en az dört parça içeriyorsa (cihaz1, interface1, cihaz2, interface2)
            device1, interface1, device2, interface2 = parts[0], parts[1], parts[2], parts[3]
            
            # İlgili router'ları bul
            node1 = nodes.get(device1)
            node2 = nodes.get(device2)
            
            if node1 and node2:
                # Interface'leri oluştur ve bağlantıyı kur
                intf1 = node1.create_interface()
                intf2 = node2.create_interface()
                lab.create_link(intf1, intf2)
                print(f"{device1} {interface1} <--> {device2} {interface2} bağlantısı oluşturuldu.")
            else:
                print(f"Hata: {device1} veya {device2} router'ı bulunamadı.")

# LAB işlem seçenekleri
def lab_operations(lab):
    print("\nLAB başlatıldı. Aşağıdaki işlemlerden birini seçebilirsiniz:")
    print("1. LAB'i durdur")
    print("2. LAB'i temizle (wipe)")
    print("3. LAB'i tamamen kaldır (remove)")
    print("4. Çıkış")

    while True:
        try:
            choice = input("Seçiminizi girin (1-4): ")
            if choice == "1":
                lab.stop()
                print("LAB durduruldu.")
            elif choice == "2":
                lab.wipe()
                print("LAB temizlendi.")
            elif choice == "3":
                lab.remove()
                print("LAB tamamen kaldırıldı.")
            elif choice == "4":
                print("Çıkış yapılıyor...")
                break
            else:
                print("Geçersiz seçim. Lütfen 1-4 arasında bir sayı girin.")
        except Exception as e:
            print(f"Bir hata oluştu: {e}")

# Ana fonksiyon
def main():
    # VIRL2 sunucusuna bağlan
    client = connect_to_virl2()

    # LAB ismi al
    lab_name = get_lab_name(client)

    # Yeni bir lab oluştur
    lab = client.create_lab(lab_name)
    print(f"'{lab_name}' isimli LAB oluşturuldu.")

    # input.txt dosyasını oku ve cihaz isimlerini al
    with open("input.txt", "r") as file:
        lines = file.readlines()[1:]  # İlk satırı (başlık satırını) atla

    # Cihaz isimlerini topla (benzersiz isimler için set kullanıyoruz)
    devices = set()
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 2:  # Satır en az iki parça içeriyorsa (cihaz adı ve interface)
            devices.add(parts[0])  # İlk cihaz
            devices.add(parts[2])  # İkinci cihaz

    # Router'ları oluştur
    nodes = create_routers(lab, devices)

    # Bağlantıları oluştur
    create_connections(lab, nodes, lines)

    # Lab'ı başlat
    print("LAB başlatılıyor...Eklenilen cihazin RAM tuketimine gore gec baslayabilir")
    lab.start()
    print("LAB başlatıldı.")

    # Node'ların ve interfacelerin durumlarını yazdır
    for node in lab.nodes():
        print(node, node.state, node.cpu_usage)
        for interface in node.interfaces():
            print(interface, interface.readpackets, interface.writepackets)

    # LAB işlem seçeneklerini sun
    lab_operations(lab)

# Ana fonksiyonu çağırarak işlemi başlat
main()
