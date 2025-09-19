---
title: Hack The Box Sherlock - PhishNet
date: 2025-09-11
tags: ["HTB", "DFIR", "phishing"]
showSummary: true
summary: Analiza maila phishingowego - "PhishNet" z HTB
draft: false
---

Czas na kolejnego sherlocka z HTB - PhishNet. Scenariusz wygląda następująco:
**An accounting team receives an urgent payment request from a known vendor. The email appears legitimate but contains a suspicious link and a .zip attachment hiding malware. Your task is to analyze the email headers, and uncover the attacker's scheme.**

Oszustwa komputerowe były najczęściej występującym rodzajem incydentu w Polsce w 2024. Z raportu CERT za poprzedni rok: `Najczęściej występującą kategorią incydentów zarejestrowanych w 2024 roku były oszustwa komputerowe. Zarejestrowano 97 995 tego typu incydentów, co stanowi 95% wszystkich obsłużonych incydentów [...] Najbardziej rozpowszechnionym rodzajem oszustw komputerowych były próby wyłudzania poufnych danych, np. loginu i hasła do poczty, strony banku, portalu społecznościowego czy innej usługi online (ang. phishing). W 2024 roku odnotowano 40 120 takich incydentów, co stanowi 39% wszystkich zarejestrowanych incydentów.`

W tym sherlocku przeanalizujemy nagłówek maila w poszukiwaniu szczegółowych informacji nt. ataku, jego źródła itp.

Otrzymaliśmy pojedynczy plik .eml do analizy.

Stworzymy testowe konto w Outlooku i przyjrzymy się treści na wirtualnej maszynie Windows 10. 

![mail_phish_1](/images/mail_phish_1.png)

Nadawca: finance@business-finance[.]com
Odbiorca: accounts@globalaccounting[.]com

Tematem maila jest niezapłacona faktura na kwotę 4750 zł za jakąś usługę. Przeanalizujmy wstępnie maila:
1. Jest to mail typu spear-phishing, wycelowany specyficznie w pracownika działu księgowości (Accounting)
2. Atakujący wykorzystuje ludzki błąd poznawczy - heurystykę dostępności. Polega na tym, że ludzie oceniają sytuacje jako bardziej prawdopodobne, jeśli łatwo potrafią sobie przypomnieć podobne przypadki z przeszłości. Pracownik księgowości zapewne miał do czynienia z wieloma niezapłaconymi fakturami w przeszłości i nie zauważył niczego podejrzanego w mailu.
3. Nadawca jest anonimowy - brak imienia i nazwiska. Jest tylko nazwa "Finance Department"
4. Atakujący stworzył dwie możliwości zarażenia ofiary - poprzez kliknięcie w link ("Download Invoice") oraz poprzez manualne pobranie i otworzenie zawartości ZIP-a
5. Atakujący używa strachu i naciska na ofiarę, że jeśli nie wykona czynności w określonym czasie, spotkają ją konsekwencje ("Please process the payment immediately to avoid late fees", "failure to act may result in penalties or service suspension")


Przeanalizujmy plik zip. Obliczmy hash i wrzućmy go do Virus Total. 

![mail_zip_hash](/images/mail_zip_hash.png)

![mail_zip_hash_VT](/images/mail_zip_hash_VT.png)

Faktycznie mamy do czynienia z plikem ZIP. Zostawmy go na razie i skupmy się na nagłówku maila

## Pytanie 1

**What is the originating IP address of the sender?**

Plik .eml otwieramy za pomocą zwykłego notatnika. Po krótkiej analizie identyfikujemy oryginalny adres IP, z którego wysłano wiadomość. 

![phishing_origin_ip](/images/phishing_origin_ip.png)

Informacje z prefixem `X-` są dodatkowymi nagłówkami niestandardowymi.

**Odpowiedź: 45.67.89.10**

![phishing_odp_1](/images/phishing_odp_1.png)

## Pytanie 2

**Which mail server relayed this email before reaching the victim?**

Pytanie jest od adres IP serwera, który przekierował maila zanim dotarł do odbiorcy.

![phishing_relay](/images/phishing_relay.png)

Adresy "Received" są zapisywanie w odwrotnej kolejności tzn. ostatni hop jest na samej górze.
`from` - nadawca
`by` - odbiorca, przez którego mail przeszedł

Komunikacja wyglądała następująco:

|                     Nadawca                      | Odbiorca                                       | Czas                                  |
| :----------------------------------------------: | ---------------------------------------------- | ------------------------------------- |
| finance@business-finance[.]com ([198.51.100.75]) | relay.business-finance[.]com ([198.51.100.45]) | Mon, 26 Feb 2025 10:05:00 +0000 (UTC) |
|  relay.business-finance[.]com ([198.51.100.45])  | mail.business-finance[.]com                    | Mon, 26 Feb 2025 10:10:00 +0000 (UTC) |
|   mail.business-finance[.]com ([203.0.113.25])   | mail.target[.]com                              | Mon, 26 Feb 2025 10:15:00 +0000 (UTC) |
E-mail trafił do mail.target.com, czyli docelowego serwera pocztowego. My jako odbiorcy widzimy adres "From" finance@business-finance[.]com. Ten nagłówek jest częścią treści wiadomości i może być modyfikowany przez wysyłającego.

**Odpowiedź: 203.0.113.25**

![phishing_odp2](/images/phishing_odp2.png)

## Pytanie 3

**What is the sender's email address?**

Znamy już odpowiedź na to pytanie. Wystarczy zobaczyć nagłówek FROM

**Odpowiedź: finance@business-finance[.]com**

![phishing_odp3](/images/phishing_odp3.png)

## Pytanie 4

**What is the 'Reply-To' email address specified in the email?**

Adres e-mail "Reply-To", to adres do którego zostanie przekierowana odpowiedź na odebranego maila.

![phising_reply_to](/images/phising_reply_to.png)

Atakujący spreparował maila tak, że wszelkie odpowiedzi trafią na adres support@business-finance[.]com

**Odpowiedź: support@business-finance[.]com** 

![phishing_odp_4](/images/phishing_odp_4.png)

## Pytanie 5

**What is the SPF (Sender Policy Framework) result for this email?**

Sender Policy Framework to mechanizm uwierzytelniania wiadomości e-mail, który chroni domenę przed spoofingiem. Działa na poziomie komunikacji między serwerami SMTP. Właściciel domeny umieszcza w ustawieniach DNS specjalny rekord SPF, który określa z jakich adresów IP można wysyłać maile z tejże domeny. Gdy serwer odbiorczy SMTP otrzymuje wiadomość, pobiera rekord SPF z DNS domeny nadawcy i sprawdza, czy adres IP nadawcy znajduje się na liście dozwolonych. W przeciwnym razie wiadomość jest odrzucana. 

![phishing_spf](/images/phishing_spf.png)

W tym przypadku serwer SMTP uznaje hosta 45.67.89.10 jako mogący wysyłać maile w imieniu domeny @business-finance.com

**Odpowiedź: Pass**

![phishing_odp_5](/images/phishing_odp_5.png)

## Pytanie 6

**What is the domain used in the phishing URL inside the email?**

Sprawdźmy jaka domena jest używana w adresie URL do pobrania malware'u.

![phishing_url](/images/phishing_url.png)

**Odpowiedź: secure.business-finance.com**

![phishing_domain](/images/phishing_domain.png)

## Pytanie 7

**What is the fake company name used in the email?**

Fałszywa nazwa firmy jest na dole maila.

![phishing_fake_company](/images/phishing_fake_company.png)

**Odpowiedź: Business Finance Ltd.**

![phishing_odp_7](/images/phishing_odp_7.png)


## Pytanie 8

**What is the name of the attachment included in the email?**

Załącznikiem jest plik ZIP

![phishing_malw_name](/images/phishing_malw_name.png)

![phishing_att](/images/phishing_att.png)

## Pytanie 9

**What is the SHA-256 hash of the attachment?**

Obliczymy hash pliku za pomocą polecenia w Powershellu
`Get-FileHash .\Invoice_2025_Payment.zip -Algorithm SHA256`

![phishing_hash](/images/phishing_hash.png)

**Odpowiedź: 8379C41239E9AF845B2AB6C27A7509AE8804D7D73E455C800A551B22BA25BB4A**

![phishing_odp_9](/images/phishing_odp_9.png)


## Pytanie 10

**What is the filename of the malicious file contained within the ZIP attachment?**

Użyjemy narzędzia `strings` do wykrycia ciągów znaków w pliku ZIP. Nie jesteśmy w stanie wypakować archiwum.

![phishing_strings](/images/phishing_strings.png)

**Odpowiedź: invoice_document.pdf.bat**

![phishing_odp_10](/images/phishing_odp_10.png)

## Pytanie 11

**Which MITRE ATT&CK techniques are associated with this attack?**

MITRE ATT&CK to ustandaryzowana baza technik wykorzystywanych przez cyberprzestępców wraz z opisami. Każda metoda ma swój unikalny kod identyfikacyjny. My szukamy ataku typu spear phishing. 

![phishing_mitre](/images/phishing_mitre.png)

**Odpowiedź: T1566.001**

![phishing_odp_11](/images/phishing_odp_11.png)

