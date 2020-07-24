from flask import Flask, render_template, request, redirect, url_for
import sqlite3 as sq
from math import floor
from random import choice, choices

db = sq.connect('db.sqlite3')
cur = db.cursor()
try:
    cur.execute("""CREATE TABLE polls (
	pollid INTEGER PRIMARY KEY,
	length INTEGER NOT NULL,
	done INTEGER NOT NULL,
	winner TEXT
);""")#0 means not done, 1 means done

except:
    pass
db.commit()
cur.close()
db.close()


app = Flask(__name__)

@app.route('/results/<int:id>', methods=['POST', 'GET'])
def results(id):
    if request.method == 'POST':
        # change the 'done' status
        # make a new template
        # implement the randomisation bit
        return 'results, post'
    else:
        db = sq.connect('db.sqlite3')
        cur = db.cursor()

        cur.execute('SELECT done FROM polls WHERE pollid = {}'.format(str(id)))
        done = cur.fetchall()[0][0]
        if done == 1:
            # fetch the winner

            cur.execute('SELECT winner FROM polls WHERE pollid = {}'.format(str(id)))
            winner = cur.fetchall()[0]

            cur.close()
            db.close()

            return render_template('finalised.html', winner=winner)
            pass
            # display the finalised results
        else:
            pass
            # if not, we continue to do things normally

        # do the dodgy js stuff to live update amount of people who have voted
        print(request.form)
        finalising=0
        try:
            finalising = request.args['finished']
        except:
            pass


        if finalising == 'yes':
            cur.execute('UPDATE polls SET done=1 WHERE pollid = {}'.format(str(id)))
            db.commit()

            cur.execute('SELECT * FROM {}'.format('poll'+str(id)))
            results = cur.fetchall()

            results = [[p[x] for x in range(1, len(p))] for p in results]
            voters = len(results)
            results = [sum(i) for i in zip(*results)]
            print(results)



            cur.execute('SELECT name FROM PRAGMA_TABLE_INFO("{}");'.format('poll' + str(id)))
            columns = cur.fetchall()
            columns = [x[0] for x in columns[1:]]

            mx = max(results)
            indices = []
            for index, x in enumerate(results):
                if x==mx:
                    indices.append(index)

            thresh = floor(0.7*mx)

            for index, x in enumerate(results):
                if x>thresh and index not in indices:
                    indices.append(index)

            winner = choices([columns[x] for x in indices], weights = [results[x] for x in indices], k=1)[0]


            # match up the sums with the films
            # do the randomisation, figure out the thresholds, how many to put into the randomiser, what to do if there's a lot of things at the top



            if mx<0:
                winner = columns[choice(indices)]

            # update the table with the winner

            print(winner)
            print(str(id))
            cur.execute('UPDATE polls SET "winner"="{1}" WHERE "pollid"={0};'.format(str(id), winner))
            db.commit()
            cur.close()
            db.close()



            print(results)

            return render_template('finalised.html', winner=winner)
        else:
            cur.close()
            db.close()
            return render_template('results.html')



@app.route('/vote/<int:id>', methods=['POST', 'GET'])
def vote(id):
    if request.method == 'POST':



        #IP adding?
        print(request.remote_addr)

        f = request.form
        print(f)

        name = 'poll'+str(id)
        columns = [x for x in f][:-1]
        values = [f[x] for x in columns]



        command = 'INSERT INTO {0} ("voterip", "{1}") VALUES ("{3}", {2});'.format(name, '","'.join(columns), ','.join(values), request.remote_addr)

        print(command)

        db = sq.connect('db.sqlite3')
        cur=db.cursor()

        cur.execute(command)

        db.commit()

        cur.close()
        db.close()


        return redirect(url_for('results', id=id))


    else:


        db = sq.connect('db.sqlite3')
        cur = db.cursor()

        cur.execute('SELECT "voterip" FROM {0}'.format('poll'+str(id)))

        ips = cur.fetchall()
        print('-'*20)
        print(ips)
        print('-' * 20)
        ips = [x[0] for x in ips]

        if request.remote_addr in ips:
            #return "You've already voted!!!"                                        FIX THIS FOR PRODUCTION!!!!!!!!!!!!
            pass

        cur.execute('SELECT "done" from polls WHERE pollid={}'.format(str(id)))
        z = cur.fetchall()[0][0]
        if z==1:
            return 'This poll has finished'



        cur.execute('SELECT name FROM PRAGMA_TABLE_INFO("{}");'.format('poll'+str(id)))
        films = cur.fetchall()
        print(films)
        films = films[1:]
        print(films)
        films = [x[0] for x in films]
        print(films)

        cur.close()
        db.close()

        return render_template('pollbox.html', films=films)


@app.route('/')
def index():
    return redirect(url_for('create'))

# @app.route('/submit/<int:id>', methods=['POST', 'GET'])
# def submit():
#     if request.method == 'POST':
#         f = request.form
#         return f['StudioGhibli']
#     else:
#         return redirect(url_for('vote'))

@app.route('/create', methods=['POST','GET'])
def create():
    if request.method == 'POST':
        f = request.form
        films = f['films']
        z=films.split('\n')
        for x in range(len(z)-1):
            z[x] = (z[x])[:len(z[x])-1]
            z[x] = z[x].strip()
        z = [x for x in z if x != '']
        print(z)

        db = sq.connect('db.sqlite3')
        cur = db.cursor()
        cur.execute('INSERT INTO polls (length, done) VALUES ({}, 0);'.format(len(z)))

        db.commit()
        c = [('"' + x + '" INTEGER NOT NULL') for x in z]
        c = ', '.join(c)

        cur.execute('SELECT pollid FROM polls ORDER BY pollid DESC LIMIT 1;')
        z = cur.fetchall()
        z=z[0][0]


        command = 'CREATE TABLE {0} ("voterip" TEXT, {1});'.format('"poll'+str(z)+'"', c)
        print(command)

        cur.execute(command)
        db.commit()

        cur.close()
        db.close()



        return redirect(url_for('vote', id=z))
    else:
        return render_template('create.html')



if __name__ == '__main__':
    app.run(debug=True)
