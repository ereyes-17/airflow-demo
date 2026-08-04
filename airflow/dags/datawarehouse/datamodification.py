from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection
import logging

logger = logging.getLogger(__name__)
TABLE = "yt_api"

def insert_row(curs: RealDictCursor, conn: connection, schema: str, row):
    # remember, staging is the raw layer and core is the refined layer
    try:
        if schema == "staging":
            video_id = "videoId"

            curs.execute(
                f"""
                    INSERT INTO {schema}.{TABLE} ("Video_ID", "Video_Title", "Video_Views", "Upload_Date", "Duration", "Likes_Count", "Comments_Count")
                    VALUES (%(videoId)s,%(title)s,%(viewCount)s,%(publishedAt)s,%(duration)s,%(likeCount)s,%(commentCount)s);
                """,
                row
            )
        else:
            video_id = "Video_ID"

            curs.execute(
                f"""
                    INSERT INTO {schema}.{TABLE} ("Video_ID", "Video_Title", "Video_Views", "Upload_Date", "Duration", "Likes_Count", "Comments_Count")
                    VALUES (%(Video_ID)s,%(Video_Title)s,%(Video_Views)s,%(Upload_Date)s,%(Duration)s,%(Likes_Count)s,%(Comments_Count)s);
                """,
                row
            )

        conn.commit()

        logger.info(f"Insterted row for video id {row[video_id]}")

    except Exception as e:
        logger.error(f"Error inserting row for video id {row[video_id]}")
        raise e

def update_rows(curs: RealDictCursor, conn: connection, schema: str, row):
    try:
        if schema == "staging":
            video_id = "videoId"
            video_title = "title"
            video_views = "viewCount"
            upload_date = "publishedAt"
            likes_count = "likeCount"
            comments_count = "commentCount"
        else:
            video_id = "Video_ID"
            video_title = "Video_Title"
            video_views = "Video_Views"
            upload_date = "Upload_Date"
            likes_count = "Likes_Count"
            comments_count = "Comments_Count"

        curs.execute(
            f"""
                UPDATE {schema}.{TABLE}
                SET "Video_Title" = %({video_title})s,
                    "Video_Views" = %({video_views})s,
                    "Upload_Date" = %({upload_date})s,
                    "Likes_Count" = %({likes_count})s,
                    "Comments_Count" = %({comments_count})s
                WHERE "Video_ID" = %({video_id})s AND "Upload_Date" = %({upload_date})s;
            """,
            row
        )

        conn.commit()

        logger.info(f"Updated record where Video_ID = {video_id} and Upload_Date = {upload_date}")
    except Exception as e:
        logger.error(f"Failed to update record where Video_ID = {video_id} and Upload_Date = {upload_date}")
        raise e

def delete_rows(curs: RealDictCursor, conn: connection, schema: str, ids_to_delete):
    try:
        ids_str = f"""({', '.join(f"'{id}'" for id in ids_to_delete)})"""

        curs.execute(
            f"""
                DELETE FROM {schema}.{TABLE}
                WHERE "Video_ID" IN {ids_str};
            """
        )

        conn.commit()

        logger.info(f"Successfully deleted rows where Video_ID IN {ids_str}")
    except Exception as e:
        logger.error(f"Failed to delete records where Video_ID IN {ids_to_delete}")
        raise e