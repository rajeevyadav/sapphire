""" Fetch events and eventdata from the eventwarehouse

    This module fetches data from the eventwarehouse, based on supplied
    start and end dates, limits and offsets.

    This module also processes data read from the event and eventdata
    tables in the eventwarehouse database. Timestamps are calculated from
    the date and time columns (remember, in GPS time!). The eventdata
    columns are processed and stored alongside the event data.

"""
import MySQLdb
import datetime
import calendar
import os

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class IntegrityError(Error):
    """Exception raised for data integrity errors.

    Attributes:
        message --- error message

    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

def get_and_process_events(station_id, table, traces, start=None,
                           stop=None, limit=None, offset=None):
    """ Get and process events from the eventwarehouse

    This is the highest level function in this module.

    This function fetches events and eventdata from the eventwarehouse
    based on start and end dates, limits and offsets. It then stores it in
    the user-supplied event table and traces array.

    Arguments:
    station_id          the HiSPARC station id
    table               the destination event table
    traces              the destination traces array
    start               a datetime instance defining the start of the
                        search interval (inclusive)
    stop                a datetime instance defining the end of the search
                        interval (inclusive)
    limit               the maximum number of events
    offset              an offset in the total event list from which point
                        on a limit number of events is being selected

    """
    events, eventdata, calculateddata = get_events(station_id, start, stop,
                                                   limit, offset)
    process_events(events, eventdata, calculateddata, table, traces)

def get_events(station_id, start=None, stop=None, limit=None, offset=None):
    """ Get events and eventdata from the eventwarehouse

    You might want to  use `get_and_process_events' instead.

    This function fetches events and eventdata from the eventwarehouse
    based on start and end dates, limits and offsets. You can pass this
    data on to the process_events function in the process_hisparc_data
    module.

    Arguments:
    station_id          the HiSPARC station id
    start               a datetime instance defining the start of the
                        search interval (inclusive)
    stop                a datetime instance defining the end of the search
                        interval (inclusive)
    limit               the maximum number of events
    offset              an offset in the total event list from which point
                        on a limit number of events is being selected

    Returns:
    events              events from the eventwarehouse event table
    eventdata           corresponding data from the eventdata tables

    """
    db = MySQLdb.connect('127.0.0.1', 'analysis', 'Data4analysis!',
                         'eventwarehouse', 3307)

    # get events from the event table
    events = get_hisparc_events(db, station_id, start, stop, limit, offset)

    if not events:
        return None, None

    # determine 'start' from the event data
    date = events[0][1]
    timedelta = events[0][2]
    start = datetime.datetime.combine(date, datetime.time()) + timedelta

    # determine 'stop' from the event data
    date = events[-1][1]
    timedelta = events[-1][2]
    stop = datetime.datetime.combine(date, datetime.time()) + timedelta

    # get the eventdata, where we don't select on event_ids, but rather
    # rely on 'start' and 'stop' instead.
    print "Time window: ", start, stop
    eventdata, calculateddata = get_hisparc_eventdata(db, station_id,
                                                      start, stop)

    db.close()

    return events, eventdata, calculateddata

def get_hisparc_events(db, station_id, start=None, stop=None, limit=None,
                       offset=None):
    """ Get data from the eventd table

    Low-level: you probably want to use `get_data'

    This function fetches data from the event table, selected by using
    the start and stop datetime instances and possibly by using a limit and
    offset. This routine is generally not called directly. Instead, use
    get_hisparc_data which calls this routine and then continues to fetch
    the corresponding eventdata.

    Arguments:
    db                  a MySQLdb connection instance to the eventwarehouse
    station_id          the HiSPARC station id
    start               a datetime instance defining the start of the
                        search interval (inclusive)
    stop                a datetime instance defining the end of the search
                        interval (inclusive)
    limit               the maximum number of events
    offset              an offset in the total event list from which point on a
                        limit number of events is being selected

    """
    cursor = db.cursor()

    sql = "SELECT event_id, date, time, nanoseconds FROM event " \
          "WHERE station_id=%d AND eventtype_id=1 " % station_id
    if start:
        sql += "AND (date > '%s' OR (date = '%s' AND time >= '%s')) " \
               % (start.date(), start.date(),
                  start.time().strftime('%H:%M:%S'))
    if stop:
        sql += "AND (date < '%s' OR (date = '%s' AND time <= '%s')) " \
               % (stop.date(), stop.date(),
                  stop.time().strftime('%H:%M:%S'))
    sql += "ORDER BY date, time, nanoseconds "
    if limit:
        if offset:
            sql += "LIMIT %d,%d" % (offset, limit)
        else:
            sql += "LIMIT %d" % limit
    cursor.execute(sql)
    results = cursor.fetchall()
    return results    

def get_hisparc_eventdata(db, station_id, start=None, stop=None):
    """ Get data from the eventdata table

    Low-level: you probably want to use `get_data'

    This function fetches data from the eventdata table, selected by using
    the start and stop datetime instances. It doesn't select using a set of
    event_id's.  This is because we may have millions of events to select
    on. This inexact match will only be inexact at the end of the data,
    where we possibly include eventdata from extra events. The reason is
    that 'start' really matches the 'start' of the events, whereas 'stop'
    has to deal with possible 'limits' and makes sure to include all
    events, at the cost of possibly including more.

    It is important to realize that YOU are responsible for making this
    work by defining correct start and stop values.
    
    Of course, this is already done for you by the get_hisparc_data
    routine, which you should probably use.

    Arguments:
    db                  a MySQLdb connection instance to the eventwarehouse
    station_id          the HiSPARC station id
    start               a datetime instance defining the start of the
                        search interval (inclusive)
    stop                a datetime instance defining the end of the search
                        interval (inclusive)

    """
    cursor = db.cursor()

    sql  = "SELECT event_id, uploadcode, doublevalue " \
           "FROM event e JOIN calculateddata USING(event_id) " \
           "JOIN calculateddatatype USING(calculateddatatype_id) " \
           "WHERE station_id=%d AND e.eventtype_id=1 " % station_id
    sql += "AND uploadcode " \
           "IN ('PH1','PH2','PH3','PH4','IN1','IN2','IN3','IN4') "
    if start:
        sql += "AND (date > '%s' OR (date = '%s' AND time >= '%s')) " \
               % (start.date(), start.date(),
                  start.time().strftime('%H:%M:%S'))
    if stop:
        sql += "AND (date < '%s' OR (date = '%s' AND time <= '%s')) " \
               % (stop.date(), stop.date(),
                  stop.time().strftime('%H:%M:%S'))
    sql += "ORDER BY date, time, nanoseconds"
    cursor.execute(sql)
    calculateddata = cursor.fetchall()

    sql  = "SELECT event_id, uploadcode, blobvalue " \
           "FROM event e JOIN eventdata USING(event_id) " \
           "JOIN eventdatatype USING(eventdatatype_id) " \
           "WHERE station_id=%d AND e.eventtype_id=1 " % station_id
    sql += "AND uploadcode " \
           "IN ('TR1', 'TR2', 'TR3', 'TR4') "
    if start:
        sql += "AND (date > '%s' OR (date = '%s' AND time >= '%s')) " \
               % (start.date(), start.date(),
                  start.time().strftime('%H:%M:%S'))
    if stop:
        sql += "AND (date < '%s' OR (date = '%s' AND time <= '%s')) " \
               % (stop.date(), stop.date(),
                  stop.time().strftime('%H:%M:%S'))
    sql += "ORDER BY date, time, nanoseconds"
    cursor.execute(sql)
    eventdata = cursor.fetchall()

    return eventdata, calculateddata


def process_events(events, eventdata, calculateddata, table, traces):
    """Do the actual data processing and storing

    You might want to  use `get_and_process_events' instead.

    This function concurrently reads the events and eventdata lists and
    builds up the event rows. When a row is complete, i.e. there are no
    more eventdata values for the current event row, it is stored in a
    pytables table.

    This is one nice long algorithmic hack. This is the price we have to
    pay to gain a speed increase of a factor of 20 or so.

    Arguments:
    events          contents from the eventwarehouse event table
    eventdata       contents from the eventwarehouse eventdata table
    calculateddata  contents from the eventwarehouse calculateddata table
    table           the destination event table
    traces          the destination traces array

    """
    tablerow = table.row
    eventdata_idx = 0
    calculateddata_idx = 0

    # First, make sure we have no 'old' eventdata records in the first few
    # rows.
    event_id = events[0][0]
    try:
        while eventdata[eventdata_idx][0] != event_id:
            eventdata_idx += 1
        while calculateddata[calculateddata_idx][0] != event_id:
            calculateddata_idx += 1
    except IndexError:
        # We've exhausted all eventdata records, there is no match!
        raise IntegrityError("Eventdata records don't match event " \
                             "records.")

    for row in events:
        # We process the events row by row
        event_id = row[0]
        date = row[1]
        timedelta = row[2]
        nanoseconds = row[3]

        # calculate the timestamp (in GPS time, not UTC time!)
        t = datetime.datetime.combine(date, datetime.time()) + timedelta
        timestamp = calendar.timegm(t.utctimetuple())

        tablerow['event_id'] = event_id
        tablerow['timestamp'] = timestamp
        tablerow['nanoseconds'] = nanoseconds
        tablerow['ext_timestamp'] = timestamp * 1e9 + nanoseconds

        # get default values for the eventdata
        data = {}
        data['pulseheights'] = tablerow['pulseheights']
        data['integrals'] = tablerow['integrals']
        data['traces'] = tablerow['traces']

        # create a list containing the current event's data records
        datalist = []
        try:
            while eventdata[eventdata_idx][0] == event_id:
                datalist.append(eventdata[eventdata_idx])
                eventdata_idx += 1
        except IndexError:
            pass

        try:
            while calculateddata[calculateddata_idx][0] == event_id:
                datalist.append(calculateddata[calculateddata_idx])
                calculateddata_idx += 1
        except IndexError:
            pass

        # process the data in this list
        for data_row in datalist:
            uploadcode = data_row[1]
            value = data_row[2]

            if uploadcode[:2] == 'PH':
                key = 'pulseheights'
            elif uploadcode[:2] == 'IN':
                key = 'integrals'
            elif uploadcode[:2] == 'TR':
                key = 'traces'
                # Store the trace in the VLArray
                traces.append(value)
                # The 'value' stored in the event table is the index to
                # the trace in the VLArray
                value = len(traces) - 1
            else:
                raise IntegrityError("Unknown datatype %s" % uploadcode)
            idx = int(uploadcode[2]) - 1 
            data[key][idx] = value

        # check to see if our new event is complete
        if (data['pulseheights'] == tablerow['pulseheights']).all() or \
           (data['integrals'] == tablerow['integrals']).all() or \
           (data['traces'] == tablerow['traces']).all():
            raise IntegrityError("Possibly missing event records.")

        tablerow['pulseheights'] = data['pulseheights']
        tablerow['integrals'] = data['integrals']
        tablerow['traces'] = data['traces']
        tablerow.append()
        # continue on to the next event

    table.flush()
