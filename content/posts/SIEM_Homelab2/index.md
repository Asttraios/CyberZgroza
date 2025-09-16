---
title: Budowanie SIEM w Proxmox - Część II
date: 2025-09-03
tags:
  - blueteam
  - siem
  - homelab
showSummary: true
summary: Stworzenie topologii logicznej i konfiguracja VLAN-ów w pfSense
draft: false
---
## Szybkie spojrzenie na Proxmox

Skoro mamy już naszego mini-PC i hypervisora Proxmox, przejdziemy do wstępnej konfiguracji. Nie będę pokazywał procesu instalacyjnego Proxmoxa, bo jest to naprawdę łatwe i powstało już na ten temat dużo tutoriali.


![24_proxmox_ui](/images/24_proxmox_ui.png)

Po udanej instalacji ukazuje nam się główny panel w Proxmox. Po lewej stronie możemy zobaczyć nasz "Datacenter", czyli nasza cała infrastruktura, najwyższy poziom w hierarchii. Tam zarządzamy globalnymi ustawieniami. "pve" natomiast jest nodem, czyli pojedynczą instancją Proxmoxa w klastrze. Nam wystarczy tylko jeden, ale w przyszłości możemy dodawać kolejne mini-PC i łączyć je w logiczną całość. Są tam również wylistowane maszyny wirtualne oraz storage. Zachęcam do szczegółowego zapoznania się z samym Proxmoxem bo oferuje naprawdę sporo możliwości. 

## Topologia 

Zanim przejdziemy do tworzenia i łączenia ze sobą maszyn wirtualnych, musimy przemyśleć i zaplanować jak w ogóle chcemy zorganizować nasz lab. Dobrym narzędziem do tworzenia schematów i szkiców jest draw.io. Darmowa aplikacja webowa, która umożliwia w łatwy sposób tworzyć takie topologie wraz z opisami i ikonami.

![siem2](/images/siem2.png)

Tak prezentuje się wstępna topologia. Wyjaśnijmy wszystko po kolei:
- Stworzę **wyizolowane, dedykowane VLANY** - każdy o innym przeznaczeniu. Np. w VLAN 5 znajdują się wyłącznie hosty Windows, a w VLAN 2 znajdują się maszynki Red Teamu, które będą przeprowadzały ataki na VLAN 4 bądź 5.
- Do zarządzania maszynkami użyjemy **Red Hata będącego w VLANie "Management"**
- Wykorzystam **Open vSwitch** - wirtualny switch dostępny natywnie w Proxmox. Głównym powodem dlaczego go wybrałem jest **port mirroring**, który jest kluczowy do monitorowania ruchu sieciowego dla SIEM. Linux Bridge niestety nie ma tej funkcji. Dzięki niej, ruch sieciowy może być kopiowany do portu monitorującego SIEM.
- **pfSense** jest odpowiedzialny za kontrolę i filtrację ruchu sieciowego dzięki regułom firewalla. Skonfiguruję w nim również VLANy.
- W VLAN 4 znajdują się maszyny wirtualne Linuxa z **podatnymi web aplikacjami do symulowanych ataków**.
- **VLAN 3 czyli SIEM** - to tutaj będziemy zarządzać i analizować logi, monitorować ruch sieciowy

Skoro już mamy plan i wiemy co i gdzie ma się znajdować, przejdźmy do konfiguracji.

## pfSense

pfSense jest systemem operacyjnym pełniącym jednocześnie funkcję routera oraz firewalla i bazuje na FreeBSD. Istnieje jeszcze inny OS - OpenSense, który jak nazwa sugeruje, też jest oprogramowaniem open-source. Ja jednak zdecydowałem się na ten pierwszy, bo mam z nim nieco większe doświadczenie, ale zachęcam do sprawdzenia obu.

W pfSense utworzymy reguły firewalla i VLANy. Obraz jest do pobrania za darmo z ich strony: hxxps://www[.]pfsense[.]org/download/

Wgrywamy ISO do wybranego przez nas **storage'u**.

![25_proxmox_storage](/images/25_proxmox_storage.png)

Przydatną rzeczą jest to, że gdy podpinamy nowy dysk do mini-PC, **w Proxmoxie możemy określić co chcemy na nim przechowywać** (np. tylko pamięć dyskowa dla VM, templatki kontenerów, obrazy iso, wszystko na raz)

Zgodnie ze schematem, będziemy potrzebowali stworzyć switch OVS, który będzie przekazywał tagowane ramki do pojedynczego interfejsu sieciowego pfSense. Następnie będą one routowane do odpowiednich VLANów. Czyli klasyczny **Router-on-a-stick**. 

Przechodzimy do naszego node'a, do zakładki "Network". Proxmox posiada domyślny linux bridge, który łączy maszyny wirtualne z fizycznym interfejsem eno1 mini-PC. Tworzymy nowy, OVS Bridge.
![1_poczatkowe_karty_sieciowe](/images/1_poczatkowe_karty_sieciowe.png)

Przypisujemy tylko nazwę "vmbr10" i klikamy "Create".

![2_tworzenie_ovs_bridge](/images/2_tworzenie_ovs_bridge.png)

Na liście urządzeń sieciowych pojawia się nasz bridge.

![3_utworzone_karty_sieciowe](/images/3_utworzone_karty_sieciowe.png)

Teraz stworzymy wirtualnego pfSense. W górnym prawym rogu panelu głównego Proxmox klikamy w "Create VM" (niebieski przycisk). W pierwszej kolejności wskazujemy node, nadajemy ID i nazwę - najlepiej krótką i rozpoznawalną.

![4_tworzenie_wirtualnego_pfsense](/images/4_tworzenie_wirtualnego_pfsense.png)

Wskazujemy wgrany obraz

![5_os_pfsense](/images/5_os_pfsense.png)

Opcje systemowe zostawiamy bez zmian. Jedynie zaznaczamy checkbox "QEMU Agent". Co to jest **QEMU Guest Agent**? To oprogramowanie instalowane w systemie operacyjnym gościa, które umożliwia lepszą komunikację między hostem Proxmox a maszyną wirtualną.

Przykładowe funkcje:

- **Informacje o systemie gościa**: CPU, pamięć, dyski

- **Wymiana danych między hostem a VM** (np. kopiowanie plików).

- Obsługa **funkcji „freeze/thaw”** podczas robienia backupów

Aby jednak agent w pełni działał, należy pobrać odpowiedni pakiet na VM. Ja ostatecznie tego nie zrobiłem, ale daję znać że istnieje taka opcja. 

![6_system_pfsense](/images/6_system_pfsense.png)

Damy sobie 16 GB wirtualnej pamięci. Wskazujemy również storage, który zostanie wykorzystany. Reszta bez zmian.

![7_disks_pfsense](/images/7_disks_pfsense.png)

Przypisujemy do maszyny 2 rdzenie procesora. Jako typ wybieramy "host", czyli bezpośrednie wykorzystanie mocy obliczeniowej procesora hosta.

![8_cpu_pfsense](/images/8_cpu_pfsense.png)

Przypisujemy 2 GB pamięci - w zupełności wystarczy

![9_memory_pfsense](/images/9_memory_pfsense.png)

Przypisujemy najpierw interfejs sieciowy podpięty do bridge'a vmbr0. Reszta bez zmian.

![10_network_pfsense](/images/10_network_pfsense.png)

Potwierdzamy wybór i dodajemy drugi interfejs sieciowy, tym razem połączony z bridgem OVS.

![26_new_interface](/images/26_new_interface.png)

Wybieramy maszynę pfSense z listy i otwieramy konsolę webową (Przycisk "Console" w górnym prawym rogu). Rozpoczynamy przypisywanie interfejsów. **W Proxmox interfejs net0 jest odpowiednikiem vtnet0 w pfSense, net1 to vtnet1** itd.

Przypisujemy interfejs WAN. vtnet0 jest podłączony do vmbr0, więc uzyska adres IP z DHCP mojego fizycznego routera (przypominam, że bridge vmbr0 łączy wirtualne maszyny z siecią fizyczną hosta). Symulować to będzie wyjście na Internet.

![pfsense_interfejs_wan](/images/pfsense_interfejs_wan.png)

Pozostały interfejs przypisujemy jako LAN. To jest ten połączony ze switchem OVS.

![2_pfsense_potwierdzenie](/images/2_pfsense_potwierdzenie.png)

Z dostępnych opcji wybieramy "Set interface(s) IP address". Przypisujemy interfejsowi LAN adres 10.0.10.1/24. Wyłączamy DHCP i nie przypisujemy adresu IPv6.

![27_pfsense_terminal](/images/27_pfsense_terminal.png)

Pozostałą konfigurację routera wykonamy przez panel webowy. Utworzymy VLANy i przypiszemy wirtualnym interfejsom adresy IP. Do tego będziemy potrzebowali nową maszynę wirtulną. Ja postawiłem na RedHat Linux, ale jakakolwiek dystrybucja z środowiskiem graficznym i przeglądarką też spełni swoją rolę. 

Przydzielamy zasoby takie jak dla pfSense, ale z wirtualnym dyskiem o pojemności 32 GB. 

![19_red_hat_manage](/images/19_red_hat_manage.png)

Przechodzimy przez proces instalacyjny i zmieniamy adres IP na odpowiadający podsieci VLAN 1 (Management).

![22_red_hat_manualne_ip](/images/22_red_hat_manualne_ip.png)

Wchodzimy w przeglądarkę Firefox i wpisujemy adres bramy domyślnej 10.0.10.1. Naszym oczom powinien ukazać się panel do logowania. Podajemy domyślne dane logowania (username:admin password:pfsense). Przechodzimy przez początkową konfigurację, pozostawiając domyślne opcje. Jedynie zmieniamy hasło na nowe.


![23_dostepny_pfsense](/images/23_dostepny_pfsense.png)

Przechodzimy do zakładki Interfaces, a następnie do VLANs


![3_pfsense_tworzenie_vlan](/images/3_pfsense_tworzenie_vlan.png)

![4_pfsense_utowrzone_vlany](/images/4_pfsense_utowrzone_vlany.png)

Po utworzeniu VLANów w zakładce Interface Assignments pojawi się możliwość przypisania wirtualnych interfejsów. Poniżej przykładowy interfejs VLANu Management.

![7_pfsense_konfig_vlan_management](/images/7_pfsense_konfig_vlan_management.png)

Utworzone VLANy z przypisanymi interefejsami,

![5_pfsense_przypisane_vlan](/images/5_pfsense_przypisane_vlan.png)

Interfejs LAN **nie powinien mieć przypisanego adresu IP**, jeśli wszystkie sieci mają być obsługiwane wyłącznie przez VLAN-y. Jeśli od razu usuniemy adresu z LAN i nie mamy jeszcze skonfigurowanych VLAN-ów z adresem i dostępem, stracimy możliwość zalogowania się przez GUI do panelu pfSense.

Powinniśmy zrobić to w następującej kolejności:

-  Najpierw utworzyć VLAN, przypisać mu adres IP i reguły dostępu.

- Zweryfikować, że możemy się zalogować przez ten VLAN.

- Dopiero wtedy usunąć adres z interfejsu rodzica (parent interface)


![6_pfsense_usuniecie_ip](/images/6_pfsense_usuniecie_ip.png)


Kiedy już mamy utworzone VLANy, możemy przejść do postawienia maszyny wirtualnej Security Onion. O tym w następnej i jednocześnie ostatniej części.