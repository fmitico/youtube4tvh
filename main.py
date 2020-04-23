from lib.m3uhandler import M3uHandler
from lib.youtubehandler import YoutubeHandler
from argparse import ArgumentParser


def cli():
    ap = ArgumentParser()
    ap.add_argument("--apikey",
                    type=str,
                    required=True,
                    help="your API KEY to use the Youtube API.")
    ap.add_argument("--apiurl",
                    type=str,
                    default="https://www.googleapis.com/youtube/v3/",
                    required=False,
                    help="base URL of the Youtube API. default is the Youtube API v3.")
    ap.add_argument("--channelid",
                    required=False,
                    type=str,
                    help="ID of a channel with a live-stream.")
    ap.add_argument("--channellogo",
                    required=False,
                    type=str,
                    help="URL of the channel's LOGO.")
    ap.add_argument("--channelname",
                    required=True,
                    type=str,
                    help="NAME of the channel with a live-stream.")
    ap.add_argument("--channelurl",
                    required=False,
                    type=str,
                    help="URL of a channel with a live-stream.")
    ap.add_argument("--inputm3u",
                    required=False,
                    type=str,
                    help="the /path/to/input.m3u. used to import data from existing m3u.")
    ap.add_argument("--outputm3u",
                    required=False,
                    default="output.m3u",
                    type=str,
                    help="the /path/to/output.m3u. default is output.m3u.")
    ap.add_argument("--inputcsv",
                    required=False,
                    type=str,
                    help="the /path/to/input.csv.  used to import data from existing csv.")
    ap.add_argument("--outputcsv",
                    required=False,
                    default="output.csv",
                    type=str,
                    help="the /path/to/output.csv. default is output.csv.")
    ap.add_argument("--pathbash",
                    required=False,
                    default="/bin/bash",
                    type=str,
                    help="the absolute /path/to/bash executable. default is /bin/bash.")
    ap.add_argument("--pathsh",
                    required=False,
                    default="/opt/youtubelivem3u/streamlink.sh",
                    type=str,
                    help="the absolute /path/to/streamlink.sh. default is /opt/youtubelivem3u/streamlink.sh.")
    return vars(ap.parse_args())


def main():
    # YOUTUBE API HANDLER
    youtube = YoutubeHandler(args_cli["apiurl"],
                             args_cli["apikey"],
                             args_cli["channelid"],
                             args_cli["channelurl"],
                             args_cli["channelname"],
                             args_cli["channellogo"])
    # Validate api key
    print("[INFO] Validating the Youtube API key...")
    if not youtube.validate_api():
        exit()
    # Find channel id
    if not args_cli["channelid"]:
        print("[INFO] Retrieving the channel ID using the channel NAME provided...")
        args_cli["channelid"] = youtube.find_id()
    # Find channel logo
    if not args_cli["channellogo"]:
        print("[INFO] Retrieving the URL of the channel's default logo...")
        args_cli["channellogo"] = youtube.find_logo()
    print("[INFO] Retrieving info from the channel's live-stream...")
    # Find info from the channel's live-stream
    stream = youtube.find_stream()

    # M3U HANDLER
    m3u = M3uHandler(args_cli["inputm3u"],
                     args_cli["outputm3u"],
                     args_cli["inputcsv"],
                     args_cli["outputcsv"])
    m3u_parameters = {
        "channelid": args_cli["channelid"],
        "channelname": args_cli["channelname"],
        "channelcountry": stream["region"],
        "channellogo": args_cli["channellogo"],
        "pathbash": args_cli["pathbash"],
        "pathsh": args_cli["pathsh"],
        "url": stream["url"]
    }
    # Parse existing input m3u file
    if args_cli["inputm3u"]:
        print("[INFO] User provided an input M3U playlist at {}.  "
              "Will try to parse it and create a data frame...".format(args_cli["inputm3u"]))
        m3u_df = m3u.parse()
        if m3u_df is None:
            print("[INFO] Generating an empty data frame...")
            m3u_df = m3u.template()
    # Else, create a template data frame
    elif not args_cli["inputm3u"]:
        print("[INFO] Did not find an input M3U playlist.  "
              "Generating an empty data frame...")
        m3u_df = m3u.template()
    # Append or update data frame
    if m3u_df.empty:
        print("[INFO] Appending stream info to data frame...")
        m3u_df = m3u.append(m3u_df, **m3u_parameters)
    elif not m3u_df.empty:
        # Check if the channel id exists in the data frame
        chboolean = m3u.search(m3u_df, "tvg-id", args_cli["channelid"])
        if chboolean:
            print("[INFO] Found the same channel on {}. "
                  "Updating its url in the data frame...".format(args_cli["inputm3u"], args_cli["outputm3u"]))
            m3u_df, upboolean = m3u.update(m3u_df, **m3u_parameters)
            # Check if update() returned None owing to an error while updating channel data
            if not upboolean:
                print("[INFO] It seems update() failed. "
                      "Will try to append the channel info to {} instead...".format(args_cli["outputm3u"]))
                m3u_df = m3u.append(m3u_df, **m3u_parameters)
        elif not chboolean:
            print("[INFO] Did not find the same channel on {}. "
                  "Will append the channel info to {}...".format(args_cli["inputm3u"], args_cli["outputm3u"]))
            m3u_df = m3u.append(m3u_df, **m3u_parameters)
    # Consolidate m3u data frame to a .m3u file
    print("[INFO] Writing data frame to .m3u file...")
    m3u.write(m3u_df)
    print("[INFO] Done!")
    print("[INFO] Writing data frame to .csv file...")
    m3u.export_csv(m3u_df)
    print("[INFO] Done!")
    print("[INFO] We're all done here. Bye!")
    exit()


if __name__ == "__main__":
    args_cli = cli()
    main()
