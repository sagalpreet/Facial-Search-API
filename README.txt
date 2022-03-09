Submitter name: Sagalpreet Singh
Roll No.: 2019csb1113
Course: CS305

=================================

1. What does this program do

This is an implementation of an api service to perform facial search on a database of images. API provides the following key functionalities:
- Insert Image in Database
- Upload Image for facial recognition
- Upload images in bulk as a zip file
- Get information regarding an image from its image id

The api has automated unit tests for testing. (86 % coverage)

2. A description of how this program works (i.e. its logic)

Database Engine Used: PostgreSQL
Test Set: LFW
Libraries/Frameworks: FastAPI

Schema Design:

id serial primary key, 
name varchar(100), 
path varchar(200),
encoding1 cube, 
encoding2 cube, 
metadata varchar(2000),
upload_time timestamp

Insert an image:
- API receives a post request in form of an image
- The file uploaded is checked for its content type to be "jpg"
- The image name is extracted as it is the label for this image
- Metadata is extracted from the image
- The image is stored in the file system
- The image encoding is obtained
- The encoding of the image, along with the path on file system
- On successful insertion, commit is made to database otherwise changes are rolled back
- Response is sent back

Storing encoding:
- Encoding is an array of 128 elements
- Cube in postgres allows only 100 elements by default
- So, we split the array into two cube elements and store

Insert images in bulk:
- Similar to inserting an image with slight modifications to boost performance
- Commit is made only after all the images are uploaded
- In case of fail, any changes made thus far are rolled back

Facial Recognition:
Image uploaded is temporarily stored in file system
The image is read for encoding
Euclidean distance of this encoding is done with all the existing encodings
Top k matches are returned as per specified k and tolerance
If less than k matches are obtained under given tolerance, then they are returned

Fetching information:
Information regarding date of upload, metadata etc. are extracted corresponding to given face id

Exceptions are handled at all database transactions.
SOLID principles are followed:
- Single Responsibility: Separate classes for database and API Design
- Open-Closed Principle: The existing Database object is closed for modification but open to addition

3. How to compile and run this program

i) Install dependencies listed in requirements.txt

ii) Run unit tests with code coverage
> coverage run -m pytest
> coverage html

iii) Database configurations can be set in /db.config

iv) Running the server (run the command from /src/api/):
> uvicorn main:app
// host and port can be specified along with other arguments like logging level
// uvicorn documentation can be referred for the same
