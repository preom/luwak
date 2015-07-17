DROP TABLE IF EXISTS records;
CREATE TABLE records(filename text not null unique, 
                     modified timestamp not null,
                     FOREIGN KEY(filename) REFERENCES meta(filename));

DROP TABLE IF EXISTS meta;
CREATE TABLE meta(filename text not null unique,
                  title text not null unique, 
                  nextFilename text,
                  prevFilename text, 
                  category text,
                  created timestamp not null,
                  PRIMARY KEY(filename));

DROP TABLE IF EXISTS tags;
CREATE TABLE tags (id INTEGER, 
                   filename text,
                   tag text not null,
                   PRIMARY KEY(id),
                   FOREIGN KEY(filename) references meta(filename));
select * from records;

