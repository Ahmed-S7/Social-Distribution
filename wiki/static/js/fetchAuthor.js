export async function retrieveAuthor(AUTHOR_ID){
            const response = await fetch(AUTHOR_ID);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const author = await response.json();
            console.log(author);
            console.log(`RESPONSE STATUS CODE: ${response.status}`);
            return author;
          }