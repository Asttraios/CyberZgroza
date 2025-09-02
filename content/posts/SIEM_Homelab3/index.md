---
title: "Budowanie SIEM w Proxmox - Część III"
date: 2025-09-02
tags: ["blueteam", "siem", "homelab"]
showSummary: true
summary: "Instalacja i konfiguracja Security Onion. Port mirroring w Proxmox"
draft: false
---

W ostatniej części miniserii o tworzeniu podstawowego SIEM-a przyjrzymy się szczegółom Security Onion oraz postawimy go w utworzonym labie.

## O Security Onion słów kilka

**Security Onion** można w dużym skrócie określić jako Kali Linux, tyle że dla Blue Teamu. W 2009 projekt został udostępniony publicznie za darmo przez Douga Burksa, weterana sił powietrznych Stanów Zjednoczonych. Security Onion jest **darmową, open-source dystrybucją Linuxa, w której skład wchodzą preinstalowane narzędzia do m.in. intrusion prevention & detection, monitorowania ruchu sieciowego, łatwego zbierania, zarządzania i analizowania logów, threat huntingu**. Do ważnych funkcjonalności należą również:

- łatwy i szybki deploy
- analiza logów usług w chmurze
- korelacja zdarzeń
- dashboardy
- możliwość integracji z EDR (Endpoint Detection & Response)
- możliwość tworzenia case'ów
- Gotowy Playbook, czyli zestaw reguł i instrukcji pomagających szybciej zidentyfikować i zniwelować zagrożenie

W arsenale security onion znajdziemy m.in.:
- **Suricata** - NIDS & NIPS, służy do wykrywania oraz blokowania szkodliwego ruchu sieciowego na podstawie sygnatur
- **Zeek** - narzędzie do monitorowania ruchu sieciowego, zapewnia bardziej szczegółowe logi o przesłanych pakietach m.in. protokoły, żądania, sesje, pliki. Nie działa na podstawie sygnatur jak Suricata, ale w połączeniu dają pełniejszy obraz podejrzanego ruchu sieciowego
- **Strelka** - system skanowania i analizy plików. Jego głównym zadaniem jest przetwarzanie plików wyodrębnionych z ruchu sieciowego lub innych źródeł i generowanie szczegółowych metadanych do analizy
- **Elastic Stack** - Elasticsearch, Kibana, Logstash. Znana trójka do zbierania, analizowania, korelowania i zarządzania logami
- **Stenographer** - przechwytywanie i analiza pakietów, wydajniejszy niż Wireshark w sieciach o dużej przepustowości
- **Elastic Agent** - zastąpił Beatsy, agent endpointowy zbierający w czasie rzeczywistym logi systemowe, aplikacji, procesów. 
- **Cyberchef** - narzędzie do m.in. kodowania/dekodowania, szyfrowania/deszyfrowania danych

Narzędzia wykorzystywane w Security Onion są open-source. 

## Deployment i wymagania

Jak wspominałem wyżej, jedną z kluczowych cech SO jest szybkość deploymentu i zautomatyzowana instalacja, nieróżniąca się poziomem skomplikowania od innych popularnych dystrybucji Linuxa. Security Onion możemy postawić na **4 sposoby**:
- **Import** - w tym trybie nie ma możliwości monitorowania ruchu sieciowego na żywo. Można jedynie importować zrzuty PCAP do analizy
- **Evaluation** - wersja demonstrująca możliwości narzędzia, nie jest przeznaczona do działania w produkcji
- **Standalone** - samodzielna instancja Security Onion, w pełni gotowa do pracy w środowisku produkcyjnym. Monitoruje i analizuje ruch sieciowy na żywo. Wymaga dużo zasobów.
- **Distributed** - rozproszona, pełna wersja, podzielona na nody. W pierwszej kolejności konfigurujemy node zarządzający, następnie dołączamy następne, pełniące różne funkcje. 

Oficjalne wymagania sprzętowe dla wersji Standalone:
- **4 CPU cores**
- **24 GB RAM**
- **Pamięć masowa min. 200 GB**
- **2 karty sieciowe**

Jak na jedną maszynkę to dość sporo, dlatego w pierwszej części podkreślałem, że bardzo ważna jest modułowość mini-PC i możliwość zmiany komponentów. Obecnie mam 32 GB, ale spróbujemy przypisać tylko 20 GB RAM-u.

## Instalacja

Pobieramy obraz z oficjalnej strony Security Onion i wrzucamy go do storage'u w Proxmox tak samo jak w przypadku poprzednich maszyn. Przy stawianiu maszyny należy pamiętać, że **potrzebuje dwóch interfejsów sieciowych** - do zarządzania oraz do monitorowania ruchu sieciowego. Wybieramy połączenie ze switchem vmbr10 (nasz "OVS Bridge"). W przypadku interfejsu monitorującego wyłączamy firewall. Natomiast w konfiguracji interfejsu zarządzającego zaznaczamy, że ramki mają mieć przypisany tag 3 (VLAN 3 SIEM). Pamiętamy o przypisaniu odpowiedniej ilości zasobów.

![28_SO_hardware](/images/28_SO_hardware.png)

![29_SO_firewall_off](/images/29_SO_firewall_off.png)

Uruchamiamy maszynę wirtualną i przechodzimy przez prostą konfigurację. Poniżej wstawiam kilka ważniejszych ustawień.

![security_onion_welcome](/images/security_onion_welcome.png)

Wybieramy standardową instalację.

![sec_onion_standard_install](/images/sec_onion_standard_install.png)

Wybieramy wersję Standalone

![sec_onion_standalone](/images/sec_onion_standalone.png)

W moim przypadku **SIEM nie ma dostępu do Internetu**. Wybieram opcję "Airgap"- w cyberbezpieczeństwie pojęcie to oznacza po prostu, że host jest fizycznie odizolowany od niezabezpieczonych sieci - w tym przypadku od Internetu. Jeśli będziemy chcieli w przyszłości zaktualizować SO wraz z regułami, wystarczy że wgramy nowy obraz ISO. 

![sec_onion_airgrap](/images/sec_onion_airgrap.png)

Wybieramy interfejs, który da nam dostęp do webowego panelu zarządzającego.

![sec_onion_managge_interface](/images/sec_onion_managge_interface.png)

Przypisujemy adres IP w naszym VLAN-ie. Zdecydowałem się na 10.0.30.10/24

![sec_onion_ip](/images/sec_onion_ip.png)

Podajemy adres IP bramy domyślnej.

![sec_onion_def_gate](/images/sec_onion_def_gate.png)

Domenę DNS zostawiam domyślną.

![sec_onion_domain](/images/sec_onion_domain.png)

Wpisujemy adres e-mail do logowania się do panelu webowego oraz do Kibany. Nie musi być prawdziwy.

![sec_onion_email](/images/sec_onion_email.png)

Jako metodę dostępu do panelu webowego wybrałem adres IP.

![sec_onion_web_ip_access](/images/sec_onion_web_ip_access.png)

Teraz wskażemy sieć VLAN 1 (Management), żebyśmy mogli z niej uzyskać dostęp do panelu webowego. Z żadnego innego VLAN-a nie dostaniemy się do niego.

![sec_onion_web_access_external](/images/sec_onion_web_access_external.png)

Podsumowanie naszych wyborów.

![sec_onion_agree](/images/sec_onion_agree.png)

![sec_onion_ready_to_boot](/images/sec_onion_ready_to_boot.png)

Po wpisaniu adresu IP hosta Security Onion w przeglądarkę na Red Hat (VLAN 1), ukazuje nam się panel logowania. Wpisujemy wcześniej podany e-mail i utoworzone hasło.

![sec_onion_first_login](/images/sec_onion_first_login.png)

Sukces! Właśnie postawiliśmy świeżego Security Onion. Jak możecie zauważyć mamy naprawdę sporo logów, dashboardów i zakładek. 

![security_onion_ready](/images/security_onion_ready.png)

## Port mirroring

Do poprawnego działania SO została nam jeszcze tylko jedna ważna rzecz do skonfigurowania - port mirroring. Jest to **funkcja przełączników (w naszym przypadku Open vSwitch), która pozwala na kopiowanie ruchu z jednego lub wielu interfejsów do interfejsu docelowego w celu analizy tego ruchu**. Tym interfejsem docelowym jest interfejs monitorujący w Security Onion. W terminalu Proxmoxa skonfigurujemy go ręcznie, ponieważ ta funkcja nie jest domyślnie włączona gdy wskazujemy interfejs monitorujący podczas instalacji SO. 

W shellu Proxmoxa wpisujemy polecenie "ip a", aby zobaczyć wszystkie interfejsy w Proxmox, również te wirtualne. Szukamy interfejsu tap103i1 (103 to ID maszyny wirtualnej SO, i1 to interfejs nr. 1, czyli monitorujący).

![tap_interface](/images/tap_interface.png)

Wpisujemy teraz polecenie ustawiające ten interfejs jako odbiorca mirrorowanego ruchu.

**`-- --id=@p get port tap103i1`**

- Pobieramy obiekt portu `tap103i1`

- Nadajemy mu alias `@p`, żeby łatwiej się do niego odwoływać.


 **`-- --id=@m create mirror name=siemspan select-all=true output-port=@p`**

- Tworzymy nowy obiekt typu **Mirror** o nazwie `siemspan`.

- `select-all=true` - mirror obejmuje **cały ruch** na switchu.

- `output-port=@p` - cały ten sklonowany ruch zostanie wysłany do portu monitorującego `tap103i1`


**`-- set bridge vmbr10 mirrors=@m`**

- Do bridge’a `vmbr10` przypisujemy właśnie utworzony mirror `@m`.

- Dzięki temu ruch z bridge’a zaczyna być kopiowany zgodnie z regułami, które podałeś w punkcie 2.


![proxmox_port_mirroring_command](/images/proxmox_port_mirroring_command.png)

Jest tylko jedno ALE. Port mirroring nie jest trwały i po **wyłączeniu** hosta Proxmoxa lub samej maszyny Security Onion trzeba wpisać polecenie na nowo (po reboocie SO port mirroring nadal działa). Czemu tak się dzieje? Okazuje się, że konfiguracja port mirroringu wprowadzona poleceniem ovs-vsctl zapisywana jest w **OVSDB** (baza danych Open vSwitch) tylko wtedy, gdy obiekt (np. port lub bridge) faktycznie istnieje w danej chwili. Gdy host Proxmox zostanie zrestartowany, wszystkie dynamiczne interfejsy typu 'tap' znikają i pojawiają się ponownie dopiero w momencie startu maszyn wirtualnych. Ponieważ mirroring w OVS jest powiązany nie z samą nazwą interfejsu (tap103i1), ale z jego **UUID**, po starcie hosta OVS „gubi” ten obiekt i mirror przestaje działać.

Natomiast **zwykły reboot Security Onion nie powoduje zmian** - port mirroring nadal działa. Problem pojawia się dopiero wtedy, gdy OVS sam jest restartowany (np. wraz z całym hostem). Poniżej wylistowałem dane interfejsu monitorującego, do którego spływa ruch sieciowy. Widać na nim aktualne UUID. Po wpisaniu polecenia 'reboot' w shellu Security Onion, UUID pozostaje bez zmian.

![tap_uuid_1](/images/tap_uuid_1.png)

Sprawdźmy jednak co się stanie, gdy wymusimy wyłączenie maszyny poprzez przycisk 'Shutdown' w panelu Proxmox.

![tap_uuid_2](/images/tap_uuid_2.png)

Jak widać sama nazwa interfejsu pozostaje bez zmian, ale zmieniło się UUID. Jak napisałem wcześniej, **OVS "skupia się" na UUID, nie nazwie. Stąd port mirroring nie działa, bo teoretycznie interfejs, na którym działał pierwotnie, nie istnieje.**

Za pomocą tcpdump sprawdźmy czy interfejs monitorujący otrzymuje kopię ruchu sieciowego. Wyślemy pinga z testowej maszyny RedHat (VLAN 1) do maszyny Xubuntu (VLAN 2).

![redhat_xubuntu_ping](/images/redhat_xubuntu_ping.png)

![SO_listening_interface_test](/images/SO_listening_interface_test.png)

Faktycznie - nic się nie pojawiło. Wpiszmy ponownie na hoście Proxmoxa polecenie konfigurujące port mirroring i sprawdźmy, czy tym razem odbieramy skopiowany ruch sieciowy.

![second_redhat_xubuntu_ping](/images/second_redhat_xubuntu_ping.png)

![so_tcpdump_pings](/images/so_tcpdump_pings.png)

## Hookscript

Jak widać, tym razem wszystko działa poprawnie. No dobra, ale czy serio będziemy wpisywać to polecenie ręcznie? Na szczęście Proxmox ma **możliwość tworzenia hookscriptów, czyli skryptów które są wykonywane w określonym momencie życia maszyny wirtulanej** (tuż przed startem, zaraz po starcie, tuż przed zatrzymaniem, zaraz po zatrzymaniu).  Nasze polecenie zostanie uruchomione w fazie zaraz po starcie, a zaraz po zatrzymaniu usuniemy zbędne mirrory związane z bridgem vmbr10. Proxmox wykonuje skrypt podczas każdej z faz z dwoma argumantami - ID maszyny oraz faza jej życia. Np. `/var/lib/vz/snippets/so-mirror-hook.sh 201 pre-start`

```
# Tworzymy katalog w /var/lib/vz o nazwie snippets

mkdir /var/lib/vz/snippets

# Tworzymy hookscript w nowym katalogu. Możemy skorzystać z przykładowego 
# /usr/share/pve-docs/examples/guest-example-hookscript.pl

nano /var/lib/vz/snippets/portmirror_hookscript.pl

# Dodajemy uprawnienie pozwalające na wykonanie

chmod +x /var/lib/vz/snippets/portmirror_hookscript.pl

# Przypisujemy go do maszyny wirtualnej Security Onion

qm set 103 --hookscript local:snippets/portmirror_hookscript.pl
```

Skrypt:
```
#!/usr/bin/perl

use strict;
use warnings;

print "GUEST HOOK: " . join(' ', @ARGV). "\n";

my $vmid  = shift;   
my $phase = shift;   

if ($phase eq 'pre-start') {
    print "$vmid is starting, doing preparations.\n";

} elsif ($phase eq 'post-start') {
    print "$vmid started successfully.\n";

    if ($vmid == 103) {
        print "Configuring port mirror for Security Onion (VM $vmid)...\n";

        my $cmd = "ovs-vsctl " .
                  "-- --id=\@p get Port tap${vmid}i1 " .
                  "-- --id=\@m create Mirror name=siemspan select-all=true output-port=\@p " .
                  "-- set Bridge vmbr10 mirrors=\@m";

        system($cmd) == 0
            or warn "Failed to execute ovs-vsctl command: $!\n";
    }

} elsif ($phase eq 'pre-stop') {
    print "$vmid will be stopped.\n";

} elsif ($phase eq 'post-stop') {
    print "$vmid stopped. Doing cleanup.\n";

    if ($vmid == 103) {
        print "Removing port mirror for Security Onion (VM $vmid)...\n";
        system("ovs-vsctl clear Bridge vmbr10 mirrors") == 0
            or warn "Failed to remove mirror: $!\n";
    }

} else {
    die "got unknown phase '$phase'\n";
}

```

Wyłączymy i włączymy ponownie Security Onion i sprawdzimy za pomocą tcpdump, czy skopiowany ruch jest odbierany.

![os_hookscript](/images/os_hookscript.png)

Jak widać działa - **udało nam się zautomatyzować poprawnie działający port mirroring**. Dzięki temu cały ruch sieciowy między VLAN-ami będzie mógł być analizowany.

## Posdumowanie

W tej trzyczęściowej serii stworzyliśmy szkielet infrastruktury naszego **laboratorium SOC**. Postawiliśmy i skonfigurowaliśmy **Security Onion** oraz zautomatyzowaliśmy funkcję **port mirroringu**. Hookscript dodatkowo usuwa mirrory po wyłączeniu maszyny. Mamy już solidne podstawy, aby zagłębić się w działania Security Onion i tworzyć własne symulowane ataki i na nie reagować. Ale o tym w przyszłych wpisach. Jeśli dotarłeś/aś do końca, to bardzo dziękuję za przeczytanie i mam nadzieję, że w jakiś sposób pomogłem Ci w poprawnej konfiguracji Security Onion.
