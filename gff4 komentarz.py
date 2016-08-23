from urllib.parse import quote

INVALID_LEN_CHR = 4

def normalize_chr(text):
    """
    Wyjściowe dane muszą być zawsze spójne.
        1 -> chr01
        2 -> chr02
        3 -> chr03
        chr1 -> chr01
    """
    if text.isdigit():
        return 'chr{0:02d}'.format(int(text))
    elif len(text) == INVALID_LEN_CHR:  # np. chr1
        return 'chr0{0}'.format(text[-1])
    else:
        return text


def parse_csv_document(content, field_sep, line_sep):
    """Przekształcanie postaci tekstowej na postać wygodną (w naszym przypadku to obiekty klasy CSVDocument)

    Argumenty:
        content: treść pochodząca z pliku, która zawiera dane
        filed_sep: Separator na poziomie pól
        line_sep: Separator na poziomie linie
    """
    lines = content.split(line_sep)

    # Budujemy rzedy
    rows = []
    for line in lines:
        if line.strip():  # linia musi być niepusta
            row = line.split(field_sep)
            rows.append(row)  # UWAGA: tutaj dalem tabulacje
    # rows to lista list zawierająca teksty
    if len(rows) == 0:
        return CSVDocument([], [])
    elif len(rows) == 1:
        return CSVDocument(rows[0], [])
    else:
        return CSVDocument(rows[0], rows[1:])


class CSVDocument:

    def __init__(self, headers, rows):
        """
        Atrybuty:
            headers: to lista (str) nagłówków
            rows: to jest lista list (każda wewnątrz lista to jeden wiersz)
        """
        self.headers = headers
        self.rows = rows

    def get_column_index(self, header):
        return self.headers.index(header)

    def add_column(self, index, header, calculate):
        """Dodaje kolumnę.

        Argumenty:
            index: Wskazuje nam miejsce, gdzie ma zostać osadzona kolumna.
            header: Nagłówek dla nowej kolumny.
            calculate: Funkcja, która jako argument przyjmuje wiersz i na tej podstawie produkuje wynik dla nowej kolumny.
        """
        self.headers.insert(index, header)
        # Na podstawie każdego rzędu tworzymy jedną wartość, która stanowi podstawę do zbudowania kolumny.
        for row in self.rows:
            value = calculate(row)
            row.insert(index, value)

    def get_column_indexes(self, column_names):
        indexes = []
        for name in column_names:
            try:
                indexes.append(self.headers.index(name))
            except ValueError:
                raise ValueError('Nie można odnaleźć nazwy: ' + name)
        return indexes

    def get_data(self, column_names):
        indexes = self.get_column_indexes(column_names)
        subdoc = self.make_subdocument_by_indexes(indexes)
        return subdoc.rows

    def make_subdocument_by_indexes(self, indexes):
        """Tworzymy NOWY dokument z wybranymi kolumnami.

        Argumenty:
            indexes: Indeksy kolumn, które mają zostać dołączone do nowego dokumentu.
        """
        # selekcja nagłówków na podstawie indeksów
        headers = []
        for i in indexes:
            header = self.headers[i]
            headers.append(header)

        # selekcja wartości na podstawie indeksów
        # czyli każdy wiersz będzie przetworzony
        # i z każdego wiersza wybieramy to co nas interesuje (patrz na indeksy).
        rows = []
        for row in self.rows:  # obsługa wielu linii
            new_row = []
            for i in indexes:  # obsługa pojedynczej lini
                new_row.append(row[i])
            rows.append(new_row)

        return CSVDocument(headers, rows)

    def render(self, field_sep=',', line_sep='\n'):
        """Powoduje utworzenie tekstu opisującego dokument.
        Udostępnia możliwość przestawienia separatorów na dowolne znaki.
        """
        lines = [
            field_sep.join(self.headers)  # powstaje nam linia z nagłówkami
        ]
        for row in self.rows:
            lines.append(field_sep.join(row))
        return line_sep.join(lines)

    def sort(self, index):
        self.rows.sort(key=lambda r: r[index])

    def __str__(self):
        return self.render()


def calculate_plus_100(row):
    return str(int(row[1]) + 100)


BASE_COL_COUNT = 3

# build_filename('fooboo.txt', 'x-factor')
# build_filename('fooboo.csv', 'x-factor', 'gff')  # gdy chcemy inne rozszerzenie niz csv (bazowe z pliku)

def build_filename(file_name, col_name, ext=None):
    """Funcja pomocnicza, służy do utworzenia nazwy pliku"""
    basename, extension = file_name.split('.')

    # Metoda format działa w oparciu o szablon np. '{0}-{1}'
    # i w trakcie wywołania podejemy wartości jakie wskakuje w przygotowane miejsca.
    # Tam gdzie jest 0 tam skoczy pierwszy argument, tam gdzie jest 1 skoczy drugi argument itp.


    # Czasem potrzebne jest rozszerzenie inne posiadał plik bazowy. Dlatego istnieje możliwość
    # podania opcjonalnego parametru ext. Jeśli jest inny niż None wtedy zostanie uwzględniony (np. gdy podamy gff).
    if ext:
        selected_ext = ext
    else:
        ext = extension # pewnie .txt

    return '{0}_{1}.{2}'.format(basename, col_name, selected_ext)


def save_document(file_name, csv_doc):
    with open(file_name, 'w') as doc:
        doc.write(csv_doc.render(' '))


# KROK: 4
def build_sub_files(file_name, doc, name_doc):
    """
    Na podstaiwe pierwszego pliku wiadomo ile powstanie tzn podplików.
    Jeśli pierwszy plik ma 5 kolumn to powstaje 2 pliki ponieważ 3 kolumny są bazowe.
    """
    # obliczamy ilosć kolumn, a zarazem plików jakie chcemy przetworzyć
    file_count = len(doc.headers) - BASE_COL_COUNT  # 2

    # Wykorzystujemy funkcję range do tego, żeby sztucznie wymusić ilość powtórzeń
    # w pętli. Natomiast ilość powtórzeń w tym przypadku jest zależna od tego ile jest extra kolumn.
    for index in range(file_count):  # [0, 1, ....]
        # extra_index to indeks kolumny jaką chcemy przepisać do pliku
        # Jeśli mamy 3 bazowe kolumny to ostatni bazowy element ma indeks 2.
        # Zatem, żeby odnieść się do kolejenych ekstra kolumn potrzebujemy większych indeksów
        # W tym przypadku już widzimy obliczenie wartości 3, a następnie wartości 4.
        extra_index = BASE_COL_COUNT + index  # (3 + 0, 3 + 1)

        sub_doc = doc.make_subdocument_by_indexes(
            [0, 1, 2, extra_index])  # [0, 1, 2, 3], [0, 1, 2, 4]

        # Jak wiadomo nazwa końcowego pliku jest zależna od ekstra kolumny zatem pobieramy jej nagłówek.
        col_name = doc.headers[extra_index]
        # Teraz tylko budujemy nazwę pliku.
        new_file_name = build_filename(file_name, col_name, 'gff')
        # Teraz budujemy obiekt
        gff_doc = build_gff(sub_doc, name_doc, sub_doc.headers)
        # Po to, żeby teraz go zapisać.
        gff_doc.save(new_file_name)


# ZASADA: stringi w pythonie są niemodyfikowalne
# zatem nie można jednocześnie na tej samej wartości wykonać kilku przekształceń

def normalize_csv_content(content):
    """Pomocnicza funkcja do normalizacji danych w pliku CSV.

    Jednolita struktura danych tak ułatwia dzielenie dokumentu na kawałki.
    """
    return content.replace('\t', ' ').replace('"', '')


# KROK: 3
def process_file(data_file_name, name_file_name=None):
    """Efektem tej funkcji jest stworzenie tzn. pod-plików na bazie wczytanych dokumentów CSV.

    Odczytujemy plik, parsujemy go i na jego podstawie budujemy obiekt opisujący dokument CSV.
    Czyli teraz mamy swobodny dostęp zarówno do wartości z dokumentu jaki nagłówków.

    W zależności od drugiego argumentu tej funkcji rozpatrywane jest wczytanie kolejnego dokumentu.

    W implementacji stosujemy normalizację treści odczytanej z pliku w celu nadania jednolitej struktury danych tak,
    żeby łatwiej móc je dzielić na kawałki.

    podplik: Dokument wyjściowy całego skryptu obejmujący scalone dane wraz z przekształceniem.

    Argumenty:
        data_file_name: Nazwa pliki z bazowymi/właściwymi danymi
        name_file_name: Plik z atrybutami (możliwe jest przekazanie wartości None)
    """
    # Budowanie pierwszego obiektu CSV
    with open(data_file_name) as document:
        content = normalize_csv_content(document.read())
    data_csv_doc = parse_csv_document(content, ' ', '\n')

    # Opcjonalne budowanie drugiego obiektu CSV
    if name_file_name:
        with open(name_file_name) as document:
            content = normalize_csv_content(document.read())
        name_csv_doc = parse_csv_document(content, ' ', '\n')
    else:
        name_csv_doc = None

    # Przekazanie obiektów w celu wygenerowania podplików
    build_sub_files(data_file_name, data_csv_doc, name_csv_doc)


SCORE_INDEX = 3


# self to odpowiednik this z C++/Java
# self uzywa sie w zastepstwie za miliony nazw egzemplarzy jakie stworzymy


# KROK #6
class DocumentGFF:
    version = '3.2.1'

    def __init__(self, headers, data, attributes):
        self.headers = headers
        self.rows = data
        self.attributes = attributes  # lista słowników (skocz: build_gff_document)

    def render(self):
        print(self._make_version_line())
        for row in self.rows:
            line = self._make_line(row)
            print(line)

    def save(self, filename):
        if self.attributes:
            self._save_with_attributes(filename)
        else:
            self._save_without_attributes(filename)
        # KONIEC CAŁEGO SKRYPTU

    def _save_without_attributes(self, filename):
        with open(filename, 'w') as doc:
            doc.write(self._make_version_line() + '\n')
            #print(self.attributes)
            for row in self.rows:

                # UWAGA UWAGA!!!
                if row[SCORE_INDEX] == 0:
                    pass  # jesli linia ma byc pomijana to zamiast pass wstawmy continue

                # Na podstawie rzedu, który jest listą i artrybutów, który nie ma budujemy linię (czyli tekst)
                line = self._make_line(row, {})
                doc.write(line + '\n')

    def _save_with_attributes(self, filename):
        with open(filename, 'w') as doc:
            doc.write(self._make_version_line() + '\n')
            #print(self.attributes)

            # Przy zapisie atrybutów pętla jest bardziej rozbudowana, ponieważ
            # chcemy scalać dane bazowe z atrybutami.
            # Czyli w trakcie iteracji mamy jednocześnie dostęp do rzędy oraz atrybutów, które opisują ten rząd.
            for row, row_attributes in zip(self.rows, self.attributes):
                # UWAGA UWAGA!!!
                if row[SCORE_INDEX] == 0:
                    pass  # jesli linia ma byc pomijana to zamiast pass wstawmy continue

                line = self._make_line(row, row_attributes)
                doc.write(line + '\n')

    def _make_line(self, row, attributes):
        return '{seqid}\t{source}\t{type}\t{start}\t{end}\t{score}\t{strand}\t{phase}\t{attributes}'.format(
            seqid=normalize_chr(row[0]),
            source='.',
            type='transposable_element',
            start=row[1],
            end=row[2],
            score=row[3],
            strand='.',
            phase='.',
            attributes=self._merge_attributes(attributes)
        )

    def _make_version_line(self):
        return '##gff-version {0}'.format(self.version)

    def _merge_attributes(self, attributes):
        if attributes:
            # funkcja quote - zmienia znaki na drukowalne np. spacje w %20
            return quote('Name={Name}'.format(Name=attributes['Name']))
        else:
            return '.'


# KROK #5
def build_gff(csv, name_csv, column_names):
    """Buduje obiekt typu DocumentGFF


    data = [
        [1, 1, 1], + ...
        [2, 2, 2], + ...
        [3, 3, 3], + ...
    ]

    attributes = [
        {Name: 'a'},
        {Name: 'b'},
        {Name: 'c'},
    ]

    Argumenty:
        csv: Obiekt DocumentCSV, posiada główne dane.
        name_csv: Obiekt DocumentCSV, moze byc tez wartoscia None, opisuje atrybuty.
        column_names: ???
    """
    data = csv.get_data(column_names)
    attributes = []
    if name_csv:
        for row in name_csv.rows:
            attributes.append({
                'Name': row[-1],
                # 'X': row[0]
            })
    return DocumentGFF(column_names, data, attributes)


# KROK #2
# Dane (czyli nazwy plików w krotkach) zostały kolejno
# przekazane do funkcji przetwarzającej pliki.
def main(tasks):
    """Wiele plików przetwarzamy."""
    for data_file_name, name_file_name in tasks:
        process_file(data_file_name, name_file_name)

    # Alternatywa:
    # for wiersz in tasks:
        # proces_file(wiersz[0], wiersz[1])

# KROK #1
# Punkt startowy tutaj określamy chcemy przetworzyć.
main([
    ('BZcoverage_Oryza_SR_Dagmara_GRnormreads.txt', None),
    ('BZcoverage_Oryza_SR_Dagmara_GRnormreads.txt', 'Arabido1_TE_Quesneville.txt'),
    #('Arabido_CG.txt', 'Arabido1_TE_Quesneville.txt'),
    #('Arabido_CT.txt', 'Arabido1_TE_Quesneville.txt'),
    #('Arabido_eG.txt', 'Arabido1_TE_Quesneville.txt'),
    #('Arabido_eT.txt', 'Arabido1_TE_Quesneville.txt'),
    #('Arabido_nT.txt', 'Arabido1_TE_Quesneville.txt'),
    #('Arabido_nF.txt', 'Arabido1_TE_Quesneville.txt'),
    #('Arabido_nG.txt', 'Arabido1_TE_Quesneville.txt'),
    # ('Arabido_SR1_CF.txt', ''),
    # ('Arabido_SR1_CF.txt', ''),
    # ('Arabido_SR1_CF.txt', '')
])


# # NOTKA O PARSOWANIU:
# # text = """
# # sun = słońce
# # milk = mleko
# # dog = pies
# # """

# # def parse_dict(text):
# #     result_dict = {}
# #     lines = text.split('\n')
# #     for line in lines:
# #         if '=' in line:
# #             left, right = line.split('=')
# #             result_dict[left.strip()] = right.strip()
# #     return result_dict

# # words = parse_dict(text)
# # print(id(words))
# # print(type(words))
# # print(words['milk'])
# # print(words)


# # class Car:

# #     def __init__(self, color):
# #         car.color = color

# #     def render(self):
# #         return 'Samochod koloru: {0}'.format(car.color)




# Magiczne słowa:
# continue -> przejście do kolejnej iteracji (działa tylko w pętli)
# break -> przerwanie pętli (działa tylko w pętli)
# Generalnie:
# Jeśli pętla używa tych słów należy to traktować na równi z sytuacją, że gdzieś na świecie ginie jednorożec.

# numbers = [1, 2, 3, 4, 5, 6, 7]
# for number in numbers:
#     if number % 2 == 1:
#         print(number)
