download = """
\b
\b\bExamples:
  # Basic download by title
  anicat anilist download -t "Attack on Titan"
\b
  # Download specific episodes
  anicat anilist download -t "One Piece" --episode-range "1-10"
\b
  # Download single episode
  anicat anilist download -t "Death Note" --episode-range "1"
\b
  # Download multiple specific episodes
  anicat anilist download -t "Naruto" --episode-range "1,5,10"
\b
  # Download with quality preference
  anicat anilist download -t "Death Note" --quality 1080 --episode-range "1-5"
\b
  # Download with multiple filters
  anicat anilist download -g Action -T Isekai --score-greater 80 --status RELEASING
\b
  # Download with concurrent downloads
  anicat anilist download -t "Demon Slayer" --episode-range "1-5" --max-concurrent 3
\b
  # Force redownload existing episodes
  anicat anilist download -t "Your Name" --episode-range "1" --force-redownload
\b
  # Download from a specific season and year
  anicat anilist download --season WINTER --year 2024 -s POPULARITY_DESC
\b
  # Download with genre filtering
  anicat anilist download -g Action -g Adventure --score-greater 75
\b
  # Download only completed series
  anicat anilist download -g Fantasy --status FINISHED --score-greater 75
\b
  # Download movies only
  anicat anilist download -F MOVIE -s SCORE_DESC --quality best
"""


search = """
\b
\b\bExamples:
  # Basic search by title
  anicat anilist search -t "Attack on Titan"
\b
  # Search with multiple filters
  anicat anilist search -g Action -T Isekai --score-greater 75 --status RELEASING
\b
  # Get anime with the tag of isekai
  anicat anilist search -T isekai
\b
  # Get anime of 2024 and sort by popularity, finished or releasing, not in your list
  anicat anilist search -y 2024 -s POPULARITY_DESC --status RELEASING --status FINISHED --not-on-list
\b
  # Get anime of 2024 season WINTER
  anicat anilist search -y 2024 --season WINTER
\b
  # Get anime genre action and tag isekai,magic
  anicat anilist search -g Action -T Isekai -T Magic
\b
  # Get anime of 2024 thats finished airing
  anicat anilist search -y 2024 -S FINISHED
\b
  # Get the most favourite anime movies
  anicat anilist search -f MOVIE -s FAVOURITES_DESC
\b
  # Search with score and popularity filters
  anicat anilist search --score-greater 80 --popularity-greater 50000
\b
  # Search excluding certain genres and tags
  anicat anilist search --genres-not Ecchi --tags-not "Hentai"
\b
  # Search with date ranges (YYYYMMDD format)
  anicat anilist search --start-date-greater 20200101 --start-date-lesser 20241231
\b
  # Get only TV series, exclude certain statuses
  anicat anilist search -f TV --status-not CANCELLED --status-not HIATUS
\b
  # Paginated search with custom page size
  anicat anilist search -g Action --page 2 --per-page 25
\b
  # Search for manga specifically
  anicat anilist search --media-type MANGA -g Fantasy
\b
  # Complex search with multiple criteria
  anicat anilist search -t "demon" -g Action -g Supernatural --score-greater 70 --year 2020 -s SCORE_DESC
\b
  # Dump search results as JSON instead of interactive mode
  anicat anilist search -g Action --dump-json
"""


main = """
\b
\b\bExamples:
  # ---- search ----
\b
  # Basic search by title
  anicat anilist search -t "Attack on Titan"
\b
  # Search with multiple filters
  anicat anilist search -g Action -T Isekai --score-greater 75 --status RELEASING
\b
  # Get anime with the tag of isekai
  anicat anilist search -T isekai
\b
  # Get anime of 2024 and sort by popularity, finished or releasing, not in your list
  anicat anilist search -y 2024 -s POPULARITY_DESC --status RELEASING --status FINISHED --not-on-list
\b
  # Get anime of 2024 season WINTER
  anicat anilist search -y 2024 --season WINTER
\b
  # Get anime genre action and tag isekai,magic
  anicat anilist search -g Action -T Isekai -T Magic
\b
  # Get anime of 2024 thats finished airing
  anicat anilist search -y 2024 -S FINISHED
\b
  # Get the most favourite anime movies
  anicat anilist search -f MOVIE -s FAVOURITES_DESC
\b
  # Search with score and popularity filters
  anicat anilist search --score-greater 80 --popularity-greater 50000
\b
  # Search excluding certain genres and tags
  anicat anilist search --genres-not Ecchi --tags-not "Hentai"
\b
  # Search with date ranges (YYYYMMDD format)
  anicat anilist search --start-date-greater 20200101 --start-date-lesser 20241231
\b
  # Get only TV series, exclude certain statuses
  anicat anilist search -f TV --status-not CANCELLED --status-not HIATUS
\b
  # Paginated search with custom page size
  anicat anilist search -g Action --page 2 --per-page 25
\b
  # Search for manga specifically
  anicat anilist search --media-type MANGA -g Fantasy
\b
  # Complex search with multiple criteria
  anicat anilist search -t "demon" -g Action -g Supernatural --score-greater 70 --year 2020 -s SCORE_DESC
\b
  # Dump search results as JSON instead of interactive mode
  anicat anilist search -g Action --dump-json
\b
  # ---- login ----
\b
  # To sign in just run
  anicat anilist auth
\b
  # To check your login status
  anicat anilist auth --status
\b
  # To log out and erase credentials
  anicat anilist auth --logout
\b
  # ---- notifier ----
\b
  # basic form
  anicat anilist notifier
\b
  # with logging to stdout
  anicat --log anilist notifier
\b
  # with logging to a file. stored in the same place as your config
  anicat --log-file anilist notifier
"""
