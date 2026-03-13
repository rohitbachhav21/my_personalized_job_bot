import mysql.connector


class Database:

    def __init__(self, config):

        self.conn = mysql.connector.connect(
            host=config["db_host"],
            user=config["db_user"],
            password=config["db_password"],
            database=config["db_name"]
        )

        self.cursor = self.conn.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS applied_jobs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_title VARCHAR(255),
            company VARCHAR(255),
            source VARCHAR(50),
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.conn.commit()


    def job_exists(self, title, company):

        query = "SELECT id FROM applied_jobs WHERE job_title=%s AND company=%s"

        self.cursor.execute(query, (title, company))

        return self.cursor.fetchone() is not None


    def save_job(self, title, company, source):

        if self.job_exists(title, company):
            return

        query = """
        INSERT INTO applied_jobs (job_title, company, source)
        VALUES (%s,%s,%s)
        """

        self.cursor.execute(query, (title, company, source))

        self.conn.commit()

        print("Saved to database:", title)