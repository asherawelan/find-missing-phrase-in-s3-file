
# Identify S3 Files That Are Missing Phrases

When we send an automated email at work, we save the content to an 
S3 bucket for reference. For example, receipts, subscription 
notifications, etc. Recently it became apparent we'd sent some 
email containing a link that was wrong.

I wrote this script to help find the emails that had been 
sent with the wrong link.

Rather than iterate over every object in the S3 bucket (1M+), the script uses
a CSV file as the iteration source, giving the object names to check in the bucket.

This CSV file was created using a SQL query with some date clauses to define a more suitable
range of files, 25k. It was three initial columns, `filename,when_phrase,must_phrase`

Not all the emails _should_ contain the link, so I took an approach to look for the link text first, 
then if that was present to look for the link. I refactored this approach to use `when_phrase` and `must_phrase` to make it more generic.

# What it does

- Loads the CSV file
- Iterates over each line and loads the object from the defined S3 bucket
- If there is a `when_phrase` value it will make sure this exists first
- The `must_phrase` is then checked - the result is saved in a new column `correct`
- The progress of the iterations is updated in a new column `checked`
- Results are written back to the CSV file

# Preperation
- Populate a CSV file with the names of the files you wish to analyse, the `must_phrase` that should be present in the file. You can also populate the `when_phrase` too.
- Copy the `.env.example` file to `.env` and complete the variable values. 

# Execution 

-  docker-compose run python