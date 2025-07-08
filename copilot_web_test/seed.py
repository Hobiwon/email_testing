import random
import string
import datetime
from faker import Faker
from sqlalchemy import func
from webapp.database import db_session
from webapp.models import User, Email, Comment

fake = Faker()

def seed_users():
    """Creates initial users if they don't exist."""
    users_to_add = [
        {'username': 'admin', 'password': 'password'},
        {'username': 'testuser', 'password': 'password'}
    ]

    for user_data in users_to_add:
        if not User.query.filter_by(username=user_data['username']).first():
            print(f"Creating user: {user_data['username']}")
            new_user = User(username=user_data['username'])
            new_user.set_password(user_data['password'])
            db_session.add(new_user)
    
    db_session.commit()

def create_random_string(length=10):
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def seed_emails(num_senders=20, emails_per_sender_per_year=75):
    """Seeds the database with random emails from a limited set of senders."""
    users = User.query.all()
    if not users:
        print("No users found. Please seed users first.")
        return

    # Generate a list of unique sender names
    sender_names = [fake.name() for _ in range(num_senders)]
    sender_year_counter = {}
    all_new_emails = []

    print("Generating email data...")
    for user in users:
        for sender_name in sender_names:
            for year in range(datetime.datetime.now().year - 2, datetime.datetime.now().year + 1):
                for _ in range(emails_per_sender_per_year):
                    date_sent = fake.date_time_between(start_date=datetime.datetime(year, 1, 1), end_date=datetime.datetime(year, 12, 31))
                    year_short = date_sent.strftime('%y')

                    counter_key = (sender_name, year)
                    if counter_key not in sender_year_counter:
                        sender_year_counter[counter_key] = 1000
                    else:
                        sender_year_counter[counter_key] += 1
                    
                    sender_number = sender_year_counter[counter_key]

                    unique_email_id = f"{sender_name.replace(' ', '')}-{year_short}-{sender_number}"

                    body_content = fake.paragraph(nb_sentences=15)

                    new_email = Email(
                        unique_email_id=unique_email_id,
                        user_id=user.id,
                        sender_name=sender_name,
                        sender_email=f"{sender_name.replace(' ', '.').lower()}@example.com",
                        title=fake.sentence(nb_words=6),
                        body=body_content,
                        email_type=random.choice(['Work', 'Personal', 'Spam', 'Promotion']),
                        date_sent=date_sent
                    )
                    all_new_emails.append(new_email)

    db_session.add_all(all_new_emails)
    print(f"Generated {len(all_new_emails)} emails.")

    print("Injecting email references...")
    all_unique_ids = [email.unique_email_id for email in all_new_emails]

    for email in all_new_emails:
        if random.random() < 0.3 and len(all_unique_ids) > 1:
            num_references = random.randint(1, 3)
            referenced_ids = random.sample(all_unique_ids, num_references)
            
            # Store references in the 'references' column as a comma-separated string
            email.references = ",".join(referenced_ids)

            # Inject references into the body
            for ref_id in referenced_ids:
                email.body += f"\n\nReference to: {ref_id}"

    db_session.commit()
    print("Finished seeding emails and references.")

def seed_comments(num_top_level_comments=150, max_replies=5):
    """Seeds the database with random comments and replies."""
    users = User.query.all()
    emails = Email.query.all()

    if not users or not emails:
        print("Users or emails not found. Please seed them first.")
        return

    print("--- Seeding Comments ---")
    
    # 1. Create top-level comments
    top_level_comments = []
    for _ in range(num_top_level_comments):
        random_email = random.choice(emails)
        random_user = random.choice(users)
        comment = Comment(
            body=fake.paragraph(nb_sentences=random.randint(1, 4)),
            timestamp=fake.date_time_between(start_date=random_email.date_sent),
            user_id=random_user.id,
            email_id=random_email.unique_email_id,
            parent_id=None
        )
        top_level_comments.append(comment)

    db_session.add_all(top_level_comments)
    db_session.commit()
    print(f"Created {len(top_level_comments)} top-level comments.")

    # 2. Create replies
    all_replies = []
    all_comments = Comment.query.filter(Comment.parent_id.is_(None)).all()

    for parent_comment in all_comments:
        num_replies = random.randint(0, max_replies)
        for _ in range(num_replies):
            random_user = random.choice(users)
            reply = Comment(
                body=fake.paragraph(nb_sentences=random.randint(1, 3)),
                timestamp=fake.date_time_between(start_date=parent_comment.timestamp),
                user_id=random_user.id,
                email_id=parent_comment.email_id,
                parent_id=parent_comment.id
            )
            all_replies.append(reply)

    db_session.add_all(all_replies)
    db_session.commit()
    print(f"Created {len(all_replies)} replies.")
    print("Finished seeding comments.")

if __name__ == '__main__':
    # First, ensure you have the Faker library installed:
    # pip install Faker
    print("--- Seeding Database ---")
    seed_users()
    seed_emails() 
    seed_comments()
