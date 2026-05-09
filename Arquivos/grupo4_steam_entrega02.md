# Página 1

PONTIFÍCIA  UNIVERSIDADE  CATÓLICA  DE  MINAS  GERAIS   Sistemas  de  Informação          Ana  Beatriz  Costa  Viana  Gustavo  Anselmo  Santos  Silva  Nicole  Marie  Agnelo  Marques  Thiago  Caetano  Dantas       DESENVOLVIMENTO  DE  UM  PROJETO  DE  BI  Análise  de  Dados  Brasileiros  da  Steam               Belo  Horizonte  2026  

---

# Página 2

1.  INTRODUÇÃO   Ano  após  ano  é  possível  ver  o  quão  grande  é  relevante  o  mercado  de  jogos  se  torna  na  economia  
mundial,
 
tendo
 
um
 
faturamento
 
estimado
 
de
 
R$197
 
bilhões
 
em
 
2025,
 
um
 
crescimento
 
de
 
7,5%
 
com
 
relação
 
ao
 
ano
 
anterior.
 
 No  mercado  há  diferentes  publishers,  estúdios,  empresas  e  plataformas  especializadas  em  criar  e  
vender
 
este
 
segmento.
 
Sendo
 
a
 
mais
 
conhecida
 
e
 
popular,
 
Steam
 
é
 
uma
 
plataforma
 
de
 
distribuição
 
digital
 
fundada
 
em
 
2003
 
pela
 
Vale
 
Corporation,
 
tendo
 
um
 
catálogo
 
de
 
jogos
 
bem
 
expressivo,
 
bem
 
como
 
a
 
quantidade
 
de
 
usuários
 
ativos.
 Com  diferentes  gêneros  de  jogos,  percebe-se  que  cada  jogador  tem  tipos  específicos  de  preferência,  e  
isso
 
se
 
espalha
 
inclusive
 
entre
 
cada
 
região
 
do
 
globo.
 
Sendo
 
assim,
 
o
 
trabalho
 
visa,
 
ao
 
utilizar
 
da
 
base
 
de
 
dados
 
fornecida
 
pela
 
Steam,
 
fazer
 
uma
 
análise
 
do
 
mercado
 
brasileiro
 
de
 
jogos
 
dessa
 
plataforma.
  1.1  Público  alvo:    A  solução  atenderá:   ●  Desenvolvedores  de  jogos  ●  Publishers  ●  Analistas  de  dados  ●  Investidores  ●  Plataformas/Lojas  digitais  ●  Jogadores   2.  FONTES  DE  DADOS  
1.  Steam  Web  API  
●  Tipo:  API  REST  (JSON)  ●  Link: https://api.steampowered.com ●  Uso  no  projeto:  ○  Lista  de  jogos  (app_id)  ○  Dados  dos  jogos  (nome,  gênero,  preço,  etc.)  ○  Jogadores  simultâneos  em  tempo  real  
2.  SteamCharts  
●  Tipo:  Website  (HTML)  ●  Link: https://steamcharts.com ●  Uso  no  projeto:  ○  Histórico  de  jogadores  ○  Média  mensal  de  jogadores  ○  Picos  de  jogadores  ○  Crescimento  (%  gain)  
3.  SteamDB  

---

# Página 3

●  Tipo:  Website  (HTML)  ●  Link: https://steamdb.info ●  Uso  no  projeto:  ○  Histórico  de  preços  ○  Atualizações  dos  jogos  ○  Dados  adicionais  (tags,  popularidade,  etc.)  
2.1.  Dicionário  de  Dados   As  principais  tabelas  que  serão  criadas  a  partir  das  fontes  de  dados:   Tabela  1  -  dim_jogos   Campo  Tipo  Descrição  Fonte  
app_id  INT  
Identificador  único  do  jogo  na  Steam  
API  
name  VARCHAR  Nome  do  jogo  API  developer  VARCHAR  Desenvolvedor  do  jogo  API  publisher  VARCHAR  Publicadora  do  jogo  API  release_date  DATE  Data  de  lançamento  API  price  DECIMAL  Preço  atual  do  jogo  API  /  SteamDB  
is_free  BOOLEAN  
Indica  se  o  jogo  é  gratuito  
API  
genres  VARCHAR  Gêneros  do  jogo  API  tags  VARCHAR  Tags  associadas  ao  jogo  SteamDB  platforms  VARCHAR  Plataformas  suportadas  API    Tabela  2  -  player_metrics    Campo  Tipo  Descrição  Fonte  
id  INT  
Identificador  da  medição  
Interno  
app_id  INT  ID  do  jogo  Todas  date  DATE  Data  da  coleta  Todas  
current_players  INT  
Jogadores  simultâneos  atuais  
API  
avg_players  INT  
Média  mensal  de  jogadores  
SteamCharts  
peak_players  INT  
Pico  de  jogadores  no  período  
SteamCharts  
peak_24h  INT  
Pico  de  jogadores  em  24h  
SteamCharts  
all_time_peak  INT  Pico  histórico  total  SteamCharts  /  SteamDB  
gain  INT  
Crescimento/queda  mensal  
SteamCharts  

---

# Página 4

percent_gain  DECIMAL  
Percentual  de  crescimento  
SteamCharts  
 Tabela  price_history   Campo  Tipo  Descrição  Fonte  id  INT  Identificador  Interno  app_id  INT  ID  do  jogo  SteamDB  date  DATE  Data  do  registro  SteamDB  price  DECIMAL  Preço  do  jogo  SteamDB  discount  DECIMAL  Percentual  de  desconto  SteamDB  currency  VARCHAR  Moeda  SteamDB   Tabela  update_frequency  Campo  Tipo  Descrição  Fonte  id  INT  Identificador  Interno  app_id  INT  ID  do  jogo  SteamDB  update_date  DATE  Data  da  atualização  SteamDB  build_id  INT  ID  da  build  SteamDB  
size_on_disk  BIGINT  
Tamanho  do  jogo  em  disco  
SteamDB  
 Figura  1  -  Modelagem  do  Data  WareHouse  
 Fonte:  autoral   


---

# Página 5

3.  ARQUITETURA  DE  ETL   3.1.  Integrações  necessárias:  
●  Biblioteca  requests  →  consumo  de  API  ●  Biblioteca  BeautifulSoup  →  web  scraping  
 Chave  de  integração:  
●  app_id  (identificador  único  do  jogo)  
3.2.  Processo  de  integração:  
1.  Coleta-se  a  lista  de  jogos  via  API  2.  Para  cada  app_id:  ○  consulta-se  dados  na  API  ○  extrai-se  histórico  no  SteamCharts  ○  extrai-se  dados  adicionais  no  SteamDB  3.  Os  dados  são  consolidados  em  tabelas  dimensionais  e  factuais  
A  integração  entre  as  fontes  de  dados  será  realizada  por  meio  do  identificador  único  app_id,  
permitindo
 
a
 
consolidação
 
de
 
dados
 
provenientes
 
da
 
Steam
 
Web
 
API,
 
SteamCharts
 
e
 
SteamDB
 
em
 
um
 
modelo
 
unificado
 
para
 
análise.
 
3.3.  Processo  ETL   Figura  2  -  Diagrama  ETL  
 Fonte:  autoral  
Etapas:  
●  Extração  ○  API  Steam  (JSON)  ○  Scraping  SteamCharts  ○  Scraping  SteamDB  ●  Transformação  ○  limpeza  de  dados  inconsistentes  ○  padronização  de  datas  


---

# Página 6

○  conversão  de  tipos  ○  remoção  de  valores  nulos  ●  Carga  ○  Inserção  no  Data  Warehouse  utilizando  Python  
SGBD  escolhido:  
●  PostgreSQL  
  
