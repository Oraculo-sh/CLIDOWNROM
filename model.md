

# Comando e flags:
 search <query> [options]	- Search for ROMs
  --platform, -p <code>		- Filter by platform code (e.g., nes, snes, n64)
  --region, -r <code>		- Filter by region code (e.g., usa, eur, jpn)
  --max-results, -m <num>	- Maximum number of results per page (default: 100, max: 100)
  --page <num>			- Page number for pagination (default: 1)
  --help, -h			- Detalha ajuda sobre o comando e suas flags disponível.

 download <index>		- Download ROMs 
  download --romid <id>		- specific ROM ID
  download --slug <slug>	- specific ROM Slug
  --platform, -p <code>		- Filter by platform code (e.g., nes, snes, n64)
  --region, -r <code>		- Filter by region code (e.g., usa, eur, jpn)
  --no-boxart			- Baixa sem boxart
  --force, -f			- Baixa sem confirmação
  --silence, -s			- Baixa silenciosamente
  --help, -h			- Detalha ajuda sobre o comando e suas flags disponível.

 boxart <index> 		- Baixa somente a boxart
  boxart --romid <id>		- specific ROM ID
  boxart --slug <slug> 		- specific slug
  --platform, -p <code>		- Filter by platform code (e.g., nes, snes, n64)
  --region, -r <code>		- Filter by region code (e.g., usa, eur, jpn)
  --force, -f			- Baixa sem confirmação
  --silence, -s			- Baixa silenciosamente
  --help, -h			- Detalha ajuda sobre o comando e suas flags disponível.

 random [options]            	- Get random ROMs
  --count, -n <num>		- Number of ROMs to return (default: 1)
  --platform, -p <code>		- Filter by platform code (e.g., nes, snes, n64)
  --region, -r <code>		- Filter by region code (e.g., usa, eur, jpn)
  --help, -h			- Detalha ajuda sobre o comando e suas flags disponível.


# Outros Comandos Disponíveis:
  info <id|index>             - Show ROM information
  config <action> [args]      - Manage configuration (--list, --get, --help, -h)
  platforms                   - List available platforms
  regions                     - List available regions
  history [count]             - Show command history
  clear                       - Clear screen
  help                        - Show this help
  exit/quit/q                 - Exit shell

# Exemplos:
  search "Super Mario" --platform snes
  download "Super Mario" --no-boxart
  random --platform nes --count 3
  config set download.max_concurrent 4

# Modelo de Saída:

Resultados 1-10 de 100 (Página 1 de 10)
#  Título                                 ID    Platform Regions Hosts           Format Size   Score
-- -------------------------------------- ----- -------- ------- --------------- ------ ------ ------
 1 Mario Bros.                            123   nes      jp      Myrient,Mega    zip    1,8G   1.000
 2 Mario & Yoshi                          123   nes      eu      Myrient,Archive zip    1,8G   0.476
 3 Dr. Mario (NP)                         123   snes     jp      Myrient         zip    1,8G   0.476
 4 Super Mario Bros.                      123   fds      jp      Myrient         zip    1,8G   0.459
 5 Dr. Mario (Rev 1)                      123   nes      jp,us   Myrient         zip    1,8G   0.450
 6 Super Mario Bros. 2                    123   fds      jp      Myrient         zip    1,8G   0.449
 7 Mario Open Golf                        123   nes      jp      Myrient         zip    1,8G   0.444
 8 Super Mario USA                        123   nes      jp      Myrient         zip    1,8G   0.444
 9 Mario is Missing!                      123   nes      eu      Myrient         zip    1,8G   0.439
10 Mario is Missing!                      123   nes      us      Myrient         zip    1,8G   0.439
> Digite o(s) número(s) referentes as roms para baixar (separados por vírgula),
> Use [n] próxima pág, [p] pág anterior, [e] exportar resultados, [q] quit, [0] reentry: