from urllib.parse import quote

INVALID_LEN_CHR = 4

def normalize_chr(text):
    """
    The output data must always be consistent.
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
    """ Converting text form to a comfortable form( in this case the objects of class CSVDocument)
    
    Arguments:
        content: content coming from a file that contains data
        filed_sep: The separator at the field level
        line_sep: The separator at the lines level

    """
    lines = content.split(line_sep)
    
    # We build rows
    rows = []
    for line in lines:
        if line.strip():  # line must be non-null
            row = line.split(field_sep)
            rows.append(row)  # NOTE : here I gave tabs
    # rows is a list of lists containing texts
    if len(rows) == 0:
        return CSVDocument([], [])
    elif len(rows) == 1:
        return CSVDocument(rows[0], [])
    else:
        return CSVDocument(rows[0], rows[1:])

    
class CSVDocument:

    def __init__(self, headers, rows):
        """
        Atributes:
            headers: is a list (str) of headers
            rows: This is a list of lists (each list within a single line)
        """
        self.headers = headers
        self.rows = rows

    def get_column_index(self, header):
        return self.headers.index(header)

    def add_column(self, index, header, calculate):
        """adding a column.

        Arguments:
            index: shows us the place where the column should be embeded.

            header: Header for a new column.
            calculate: A function that takes a row as an argument and on this basis produces a result for the new column.

        """
        self.headers.insert(index, header)
        # Based on each row we form one value, which is the basis to build the column.

        for row in self.rows:
            value = calculate(row)
            row.insert(index, value)

    def get_column_indexes(self, column_names):
        indexes = []
        for name in column_names:
            try:
                indexes.append(self.headers.index(name))
            except ValueError:
                raise ValueError(' Name Not Found: ' + name)
        return indexes

    def get_data(self, column_names):
        indexes = self.get_column_indexes(column_names)
        subdoc = self.make_subdocument_by_indexes(indexes)
        return subdoc.rows

    def make_subdocument_by_indexes(self, indexes):
        """ We create a new document with the selected columns.

        Argumenty:
            indexes: Column indices which are to be included in the new document.
        """
        # header selection by indexes
        headers = []
        for i in indexes:
            header = self.headers[i]
            headers.append(header)

        # value selection by indexes
        # that is, each line will be processed
        # and from each row we choose what interests us (see indexes).

        rows = []
        for row in self.rows:  # support for multiple lines
            new_row = []
            for i in indexes:  # support for single line
                new_row.append(row[i])
            rows.append(new_row)

        return CSVDocument(headers, rows)

    def render(self, field_sep=',', line_sep='\n'):
        """ Creates text describing the document. It provides the ability to switch separators for any characters.
        """
        lines = [
            field_sep.join(self.headers)  # We created a line of heading        ]
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
# build_filename('fooboo.csv', 'x-factor', 'gff')  # if we want other extension than .csv ( base file )


def build_filename(file_name, col_name, ext=None):
    """ auxiliary function used to create the file name"""
    basename, extension = file_name.split('.')
    
    # Method format is based on the template for example .'{0}-{1}'
    # and during the calling out we give the values that snap into the prepared place.
    # Where there is a 0 there leaps the first argument, where 1 leaps the second argument, etc.

    
    
    # Sometimes it is necessary to have other extension than had the file base. Therefore, there is a possibility to 
    # provide an optional parameter ext. If it is different than None then it will be included (eg. If we give gff). 

    if ext:
        selected_ext = ext
    else:
        ext = extension # pewnie .txt
    
    return '{0}_{1}.{2}'.format(basename, col_name, selected_ext)


def save_document(file_name, csv_doc):
    with open(file_name, 'w') as doc:
        doc.write(csv_doc.render(' '))


# STEP: 4
def build_sub_files(file_name, doc, name_doc):
    """On the basis of the first file it is known how many subfiles will be created. If the first file has 5 columns then 2 files will be created because 3 columns are base.

    """
    # We calculate the amount of columns, and at the same time the number of files we want to process.

    file_count = len(doc.headers) - BASE_COL_COUNT  # 2
    
    # We use the function range to artificially force the number of repetitions

    # in the loop. However, the number of repetitions in this case is dependent on how many extra columns there are.

    for index in range(file_count):  # [0, 1, ....]
        # extra_index is the index of the column we want to rewrite to the file

        # If we have 3 base columns then the last base element has an index of 2.

        # Therefore, to refer to the following extra columns we need major indexes

        # In this case, we can already see the calculation of the value of 3, then the value of 4.

        extra_index = BASE_COL_COUNT + index  # (3 + 0, 3 + 1)
        
        sub_doc = doc.make_subdocument_by_indexes(
            [0, 1, 2, extra_index])  # [0, 1, 2, 3], [0, 1, 2, 4]
        
        # As we know the name of the final file is dependent on the extra column, therefore we take the header of this column.

        col_name = doc.headers[extra_index]
        # Now we only build the file name.

        new_file_name = build_filename(file_name, col_name, 'gff')
        # Now we build the object
        gff_doc = build_gff(sub_doc, name_doc, sub_doc.headers)
        # and now we save it
        gff_doc.save(new_file_name)

        
# PRINCIPLE : strings in python are non-modifiable
# therefore we can not simultaneously make several transformations on the same value 


def normalize_csv_content(content):
    """ The auxiliary function to normalize the data in a CSV file.
 
    
A uniform data structure so facilitates the division of the document into pieces.
    """
    return content.replace('\t', ' ').replace('"', '')


# STEP: 3
def process_file(data_file_name, name_file_name=None):
    """ The result of this function is creation of the so called subfiles based on the loaded CSV documents.

    
    We read the file, parse it and on its basis we build an object describing the CSV document.

    So we now have the free access to both the values of the document as to the headers.
   
    Depending on the second argument of this function, loading of another document is considered.
    
    In the implementation we use the normalization of content read from the file in order to give a uniform data structure, so that to be able more easily divide it into pieces.

    
    subfile : Output Document of the whole script including the merged data tougether with their conversion.
    
    Arguments:
        data_file_name: Name of the file with the base/relevant data

        name_file_name: The file with the attributes (it is possible to transfer the value None)

    """
    # Building of the first CSV object
    with open(data_file_name) as document:
        content = normalize_csv_content(document.read())
    data_csv_doc = parse_csv_document(content, ' ', '\n')
    
    # Optional building of the second CSV object
    if name_file_name:
        with open(name_file_name) as document:
            content = normalize_csv_content(document.read())
        name_csv_doc = parse_csv_document(content, ' ', '\n')
    else:
        name_csv_doc = None
    
    # Transmission of objects in order to generate subfiles
    build_sub_files(data_file_name, data_csv_doc, name_csv_doc)
        

SCORE_INDEX = 3


# self equivalent to this z C++/Java
# self is used as a proxy for the names of millions of copies we will create



# STEP #6
class DocumentGFF:
    version = '3.2.1'

    def __init__(self, headers, data, attributes):
        self.headers = headers
        self.rows = data
        self.attributes = attributes  # list of dictionaries (jump: build_gff_document)

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
        # END OF THE ENTIRE SCRIPT
        
    def _save_without_attributes(self, filename):
        with open(filename, 'w') as doc:
            doc.write(self._make_version_line() + '\n')
            #print(self.attributes)
            for row in self.rows:
                
                # WARNING WARNING!!!
                if row[SCORE_INDEX] == 0:
                    pass  # if the line is to be skipped instead pass insert continue

                
                # Na podstawie rzedu, który jest listą i artrybutów, który nie ma budujemy linię (czyli tekst) 
On the basis of the row which is a list and atributes and which is not we are building a line (or text)

                line = self._make_line(row, {})
                doc.write(line + '\n')
        
    def _save_with_attributes(self, filename):
        with open(filename, 'w') as doc:
            doc.write(self._make_version_line() + '\n')
            #print(self.attributes)
            
            # When writing the attributes, the loop is more complex , because

            # we want to merge the base data with attributes.

            # So during the iteration we have ssimultaneousely access to the rows and attributes that describe this rows.

            for row, row_attributes in zip(self.rows, self.attributes):
                # WARNING WARNING !!!
                if row[SCORE_INDEX] == 0:
                    pass  # if the line is to be skipped instead pass insert continue
                
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
            # function quote - changes signs on the printable eg. spaces
 into %20
            return quote('Name={Name}'.format(Name=attributes['Name']))
        else:
            return '.'

    
# STEP #5
def build_gff(csv, name_csv, column_names):
    """Builds an object of the type DocumentGFF
    
    
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
        csv: Object DocumentCSV, contains the main data.
        name_csv: object DocumentCSV, can also be the value of None, describes the attributes 

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


# STEP #2
# The data (ie, file names in tuples) were sequentially
# passed to the function processing files

def main(tasks):
    """Many files are processed."""
    for data_file_name, name_file_name in tasks:
        process_file(data_file_name, name_file_name)

    # Alternative:
    # for line in tasks:
        # proces_file(line[0], line[1])
            
# STEP #1
# Punkt startowy tutaj określamy chcemy przetworzyć. Starting point, here we define what we want to process
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


# # NOTE About parsing:
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




# Magic words:
# continue -> the transition to the next iteration (only works in a loop)

# break -> interruption of loop (only works in a loop)
# Generally: 
# if the loop uses these words it should to be equated with the situation, that somewhere in the world dies an unicorn.


# numbers = [1, 2, 3, 4, 5, 6, 7]
# for number in numbers:
#     if number % 2 == 1:
#         print(number)
