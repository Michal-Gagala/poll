from flask import Flask, render_template, request, redirect, url_for
import sqlite3 as sq
from math import floor
from random import choice, choices
from logging import info, basicConfig, INFO, warning

basicConfig(level=INFO)
info('Config Set')

db = sq.connect('db.sqlite3')
cur = db.cursor()
try:
    cur.execute("""CREATE TABLE polls (
	pollid INTEGER PRIMARY KEY,
	length INTEGER NOT NULL,
	done INTEGER NOT NULL,
	winner TEXT
);""")#0 means not done, 1 means done
    info('Database Created')
except:
    info('Database already created')

db.commit()
cur.close()
db.close()

app = Flask(__name__)

@app.route('/results/<int:id>', methods=['POST', 'GET'])
def results(id):
    if request.method == 'POST':
        warning('Someone POSTed to results?')
        # change the 'done' status
        # make a new template
        # implement the randomisation bit
        return 'results, post'
    else:
        db = sq.connect('db.sqlite3')
        cur = db.cursor()

        cur.execute('SELECT done FROM polls WHERE pollid = {}'.format(str(id)))
        done = cur.fetchall()[0][0]

        ip = request.remote_addr

        if done == 1:
            info('{} is viewing the results of poll {}'.format(ip, id))
            # fetch the winner

            cur.execute('SELECT winner FROM polls WHERE pollid = {}'.format(str(id)))
            winner = cur.fetchall()[0][0]

            cur.execute('SELECT * FROM {}'.format('poll'+str(id)))
            results = cur.fetchall()

            results = [[p[x] for x in range(1, len(p))] for p in results]
            voters = len(results)
            results = [sum(i) for i in zip(*results)]

            cur.execute('SELECT name FROM PRAGMA_TABLE_INFO("{}");'.format('poll' + str(id)))
            columns = cur.fetchall()
            columns = [x[0] for x in columns[1:]]

            cur.close()
            db.close()



            return render_template('finalised.html', winner=winner, films=columns, results=results, voteramount=voters)

            # display the finalised results
        else:
            pass
            # if not, we continue to do things normally

        # do the dodgy js stuff to live update amount of people who have voted
        #print(request.form)
        finalising=0
        try:
            finalising = request.args['finished']
        except:
            pass


        if finalising == 'yes':
            info('Poll {} is being finalised'.format(str(id)))

            cur.execute('UPDATE polls SET done=1 WHERE pollid = {}'.format(str(id)))
            db.commit()

            cur.execute('SELECT * FROM {}'.format('poll'+str(id)))
            results = cur.fetchall()

            results = [[p[x] for x in range(1, len(p))] for p in results]
            voters = len(results)
            results = [sum(i) for i in zip(*results)]

            info('The results of poll {0} are: {1}'.format(str(id), ', '.join([str(x) for x in results])))



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

            info('The winner of poll {0} is {1}'.format(str(id), winner))

            # update the table with the winner

            #print(winner)
            #print(str(id))
            cur.execute('UPDATE polls SET "winner"="{1}" WHERE "pollid"={0};'.format(str(id), winner))
            db.commit()
            cur.close()
            db.close()



            #print(results)

            return render_template('finalised.html', winner=winner, films=columns, results=results, voteramount=voters)
        else:
            cur.close()
            db.close()
            info('{} is waiting for finalisation'.format(request.remote_addr))
            return render_template('results.html')



@app.route('/vote/<int:id>', methods=['POST', 'GET'])
def vote(id):
    if request.method == 'POST':
        #IP adding?

        ip = request.remote_addr

        info('{} POSTed to vote'.format(ip))

        f = request.form

        name = 'poll'+str(id)
        columns = [x for x in f][:-1]
        values = [f[x] for x in columns]

        command = 'INSERT INTO {0} ("voterip", "{1}") VALUES ("{2}", {3});'.format(name, '","'.join(columns), ip,
                                                                                   ','.join(values))


        db = sq.connect('db.sqlite3')
        cur=db.cursor()
        cur.execute(command)
        db.commit()
        info('{} had vote added to table'.format(ip))

        cur.close()
        db.close()

        return redirect(url_for('results', id=id))
    else:


        db = sq.connect('db.sqlite3')
        cur = db.cursor()

        cur.execute('SELECT "voterip" FROM {0}'.format('poll'+str(id)))

        ips = cur.fetchall()
        #print('-'*20)
        #print(ips)
        #print('-' * 20)
        ips = [x[0] for x in ips]

        ip = request.remote_addr

        info('{0} is attempting to vote in poll number {1}. Votes have already been made by: {2}'.format(ip, str(id),', '.join(ips)))


        if ip in ips:
            info('Voter {0} has been turned away from poll number {1} to prevent duplicates'.format(ip, str(id)))
            return "You've already voted!!!"

        cur.execute('SELECT "done" from polls WHERE pollid={}'.format(str(id)))
        z = cur.fetchall()[0][0]
        if z==1:
            info('Voter {0} has been turned away because poll number {1} has concluded'.format(ip, str(id)))
            return 'This poll has finished'



        cur.execute('SELECT name FROM PRAGMA_TABLE_INFO("{}");'.format('poll'+str(id)))
        films = cur.fetchall()
        #print(films)
        films = films[1:]
        #print(films)
        films = [x[0] for x in films]
        #print(films)

        cur.close()
        db.close()

        return render_template('pollbox.html', films=films)


@app.route('/')
def index():
    info('Someone redirected from / to /create')
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



        db = sq.connect('db.sqlite3')
        cur = db.cursor()
        cur.execute('INSERT INTO polls (length, done) VALUES ({}, 0);'.format(len(z)))
        db.commit()

        info('polls updated with new poll')

        c = [('"' + x + '" INTEGER NOT NULL') for x in z]
        c = ', '.join(c)

        cur.execute('SELECT pollid FROM polls ORDER BY pollid DESC LIMIT 1;')
        z = cur.fetchall()
        z=z[0][0]

        info('Number of the poll is {}'.format(str(z)))

        command = 'CREATE TABLE {0} ("voterip" TEXT, {1});'.format('"poll'+str(z)+'"', c)

        info('Poll {} has had its table created'.format(str(z)))

        cur.execute(command)
        db.commit()

        cur.close()
        db.close()

        return redirect(url_for('vote', id=z))
    else:
        return render_template('create.html')



if __name__ == '__main__':
    app.run(debug=True)
