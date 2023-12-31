from empath import Empath
from operator import add
from pyspark.sql import SparkSession
from sys import argv

#função que tokeniza a entrada
def separa(line):
    result = []
    #caso não seja texto não tenta executar e retorna uma lista vazia
    if isinstance(line.Lyric, str):
        result = line.Lyric.lower().split(" ")
    return result
    
#nome do arquivo .csv
arq = argv[1]

#inicio da sessão Spark
spark = SparkSession\
  .builder \
  .appName("PythonWordCount") \
  .getOrCreate()

#carrega uma lista de StopWords
gist_file = open("gist_stopwords.txt", "r")
try:
    content = gist_file.read()
    stop_words = content.split(",")
    stop_words.append("")
finally:
    gist_file.close()

#lê o arquivo csv especificado no argumento selecionando a coluna Lyric que é a qual contém as letras das músicas
data = spark.read.format('csv').options(header='true', inferSchema='true') \
.load(arq)

# faz o mapping, filtrando as stopwords e fazendo o reduce logo em seguida
mapped_rdd = data.select("Lyric").rdd.flatMap (lambda line: separa(line)).filter(lambda x: x not in stop_words)\
    .map(lambda word: (word, 1)).reduceByKey (add)
#captura as 20 palavras com maior ocorrência
top20 = mapped_rdd.takeOrdered(20, key=lambda x: -x[1])
#captura apenas as palavras (keys)
top_words = set().union((key for (key, value) in top20))

#instancia o empath e analiza as 20 palavras mais recorrentes
lexicon = Empath()
my_dict = lexicon.analyze(list(top_words), normalize=True)
#captura o nome do artista
artist = data.select("Artist").first()["Artist"]
#põe a lista em ordem decrescente
sorted_dict = sorted(my_dict.items(), key=lambda x: -x[1])
#abre o arquivo de saída
out = open(artist+"_out.txt", "w")
out.write("Artist: "+artist+"\n\n")
out.write("Categories found in descending order:\n\n")
#para cada resultado positivo que o empath detecta é escrito a categoria detectada e sua pontuação em ordem decrescente
for key, value in sorted_dict:
    if value > 0:
        out.write("%s: %f\n"%(key, value))

out.close()

spark.stop()
