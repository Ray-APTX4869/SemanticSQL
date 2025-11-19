select country from airlines where airline = "jetblue airways"	flight_2
select country from airlines where airline = "jetblue airways"	flight_2
select abbreviation from airlines where airline = "jetblue airways"	flight_2
select abbreviation from airlines where airline = "jetblue airways"	flight_2
select airline, abbreviation from airlines where country = "usa"	flight_2
select airline, abbreviation from airlines where country = "usa"	flight_2
select airportcode, airportname from airports where city = "anthony"	flight_2
select airportcode, airportname from airports where city = "anthony"	flight_2
select count(*) from airlines	flight_2
select count(*) from airlines	flight_2
select count(*) from airports	flight_2
select count(*) from airports	flight_2
select count(*) from flights	flight_2
select count(*) from flights	flight_2
select airline from airlines where abbreviation = "ual"	flight_2
select airline from airlines where abbreviation = "ual "	flight_2
select count(*) from airlines where country = "usa"	flight_2
select count(*) from airlines where country = "usa"	flight_2
select city, country from airports where airportname = "alton "	flight_2
select city, country from airports where airportname = "alton airport"	flight_2
select airportname from airports where airportcode = "ako "	flight_2
select airportname from airports where airportcode = "ako"	flight_2
select airportname from airports where city = "aberdeen"	flight_2
select airportname from airports where city = "aberdeen"	flight_2
select count(*) from flights where sourceairport = "apg"	flight_2
select count(*) from flights where sourceairport = "apg"	flight_2
select count(*) from flights where destairport = "ato"	flight_2
select count(*) from flights where destairport = "ato"	flight_2
select count(*) from flights join airports on flights.sourceairport = airports.airportcode where airports.city = "aberdeen"	flight_2
select count(*) from flights join airports on flights.sourceairport = airports.airportcode where airports.city = "aberdeen"	flight_2
select count(*) from flights join airports on flights.destairport = airports.airportcode where airports.city = "aberdeen"	flight_2
select count(*) from flights join airports on flights.destairport = airports.airportcode where airports.city = "aberdeen"	flight_2
select count(*) from flights f join airports s on f.sourceairport = s.airportcode join airports d on f.destairport = d.airportcode where s.city = "aberdeen" and d.city = "ashley"	flight_2
select count(*) from flights join airports as a on flights.sourceairport = a.airportcode join airports as b on flights.destairport = b.airportcode where a.city = "aberdeen" and b.city = "ashley"	flight_2
select count(*) from flights join airlines on flights.airline = airlines.uid where airlines.airline = "jetblue airways "	flight_2
select count(*) from flights join airlines on flights.airline = airlines.uid where airlines.airline = "jetblue airways"	flight_2
select count(*) from flights join airlines on flights.airline = airlines.uid where airlines.airline = "united airlines" and flights.destairport = "asy"	flight_2
select count(*) from flights join airlines on flights.airline = airlines.uid where airlines.airline = "united airlines" and flights.destairport = "asy"	flight_2
select count(*) from flights join airlines on flights.airline = airlines.uid where airlines.airline = "united airlines " and flights.sourceairport = "ahd "	flight_2
select count(*) from flights join airlines on flights.airline = airlines.uid join airports on flights.sourceairport = airports.airportcode where airlines.airline = "united airlines" and airports.airportname = "ahd airport"	flight_2
select count(*) from flights join airlines on flights.airline = airlines.uid join airports on flights.destairport = airports.airportcode where airlines.airline = "united airlines" and airports.city = "aberdeen "	flight_2
select count(*) from flights join airlines on flights.airline = airlines.uid join airports on flights.destairport = airports.airportcode where airlines.airline = "united airlines" and airports.city = "aberdeen"	flight_2
select airports.city from flights join airports on flights.destairport = airports.airportcode group by airports.city order by count(*) desc limit 1	flight_2
select airports.city from flights join airports on flights.destairport = airports.airportcode group by airports.city order by count(*) desc limit 1	flight_2
select airports.city from flights join airports on flights.sourceairport = airports.airportcode group by airports.city order by count(*) desc limit 1	flight_2
select airports.city from airports join flights on airports.airportcode = flights.sourceairport group by airports.city order by count(*) desc limit 1	flight_2
select airportcode from (select sourceairport as airportcode from flights union all select destairport as airportcode from flights) group by airportcode order by count(*) desc limit 1	flight_2
select airportcode from (select sourceairport as airportcode from flights union all select destairport as airportcode from flights) as f group by airportcode order by count(*) desc limit 1	flight_2
select airports.airportcode from airports left join (select airport, count(*) as cnt from (select sourceairport as airport from flights union all select destairport as airport from flights) group by airport) as f on airports.airportcode = f.airport order by coalesce(f.cnt, 0) asc limit 1	flight_2
with counts as (select a.airportcode, coalesce(c.cnt, 0) as cnt from airports a left join (select airportcode, count(*) as cnt from (select sourceairport as airportcode from flights union all select destairport as airportcode from flights) t group by airportcode) c on a.airportcode = c.airportcode) select airportcode from counts where cnt = (select min(cnt) from counts)	flight_2
select airlines.airline from airlines join flights on airlines.uid = flights.airline group by airlines.airline order by count(*) desc limit 1	flight_2
select airlines.airline from flights join airlines on flights.airline = airlines.uid group by airlines.airline order by count(*) desc limit 1	flight_2
select abbreviation, country from airlines join flights on airlines.uid = flights.airline group by airlines.uid, abbreviation, country order by count(*) asc limit 1	flight_2
select airlines.abbreviation, airlines.country from airlines join flights on airlines.uid = flights.airline group by airlines.uid, airlines.abbreviation, airlines.country order by count(*) asc limit 1	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid = t2.airline where t2.sourceairport = "ahd"	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid = t2.airline where t2.sourceairport = "ahd"	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid = t2.airline where t2.destairport = "ahd "	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid = t2.airline where t2.destairport = "ahd"	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid = t2.airline where t2.sourceairport = "apg " intersect select t1.airline from airlines as t1 join flights as t2 on t1.uid = t2.airline where t2.sourceairport = "cvo "	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid = t2.airline where t2.sourceairport = "apg" intersect select t1.airline from airlines as t1 join flights as t2 on t1.uid = t2.airline where t2.sourceairport = "cvo"	flight_2
select a.airline from airlines as a join flights as f on a.uid = f.airline where f.sourceairport = "cvo " except select a.airline from airlines as a join flights as f on a.uid = f.airline where f.sourceairport = "apg "	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid = t2.airline where t2.sourceairport = "cvo" except select t1.airline from airlines as t1 join flights as t2 on t1.uid = t2.airline where t2.sourceairport = "apg"	flight_2
select airlines.airline from airlines join flights on airlines.uid = flights.airline group by airlines.airline having count(*) > = 10	flight_2
select airlines.airline from airlines join flights on airlines.uid = flights.airline group by airlines.airline having count(*) > = 10	flight_2
select airlines.airline from airlines left join flights on flights.airline = airlines.uid group by airlines.airline having count(flights.flightno) < 200	flight_2
select airlines.airline from airlines left join flights on airlines.uid = flights.airline group by airlines.uid, airlines.airline having count(flights.flightno) < 200	flight_2
select flightno from flights join airlines on flights.airline = airlines.uid where airlines.airline = "united airlines"	flight_2
select flightno from flights join airlines on flights.airline = airlines.uid where airlines.airline = "united airlines"	flight_2
select flightno from flights where sourceairport = "apg"	flight_2
select flightno from flights where sourceairport = "apg"	flight_2
select flightno from flights where destairport = "apg"	flight_2
select flightno from flights where destairport = "apg"	flight_2
select flights.flightno from flights join airports on flights.sourceairport = airports.airportcode where airports.city = "aberdeen"	flight_2
select flightno from flights join airports on flights.sourceairport = airports.airportcode where airports.city = "aberdeen"	flight_2
select flightno from flights join airports on flights.destairport = airports.airportcode where airports.city = "aberdeen"	flight_2
select flightno from flights join airports on flights.destairport = airports.airportcode where airports.city = "aberdeen"	flight_2
select count(*) from flights join airports on flights.destairport = airports.airportcode where airports.city = "aberdeen" or airports.city = "abilene"	flight_2
select count(*) from flights join airports on flights.destairport = airports.airportcode where airports.city = "aberdeen" or airports.city = "abilene"	flight_2
select airportname from airports as a where not exists (select 1 from flights as f where f.sourceairport = a.airportcode or f.destairport = a.airportcode)	flight_2
select airportname from airports as a where not exists (select 1 from flights as f1 where f1.sourceairport = a.airportcode) and not exists (select 1 from flights as f2 where f2.destairport = a.airportcode)	flight_2
select count(*) from singer	concert_singer
select count(*) from singer	concert_singer
select name, country, age from singer order by age desc	concert_singer
select name, country, age from singer order by age desc	concert_singer
select avg(age), min(age), max(age) from singer where country = "france"	concert_singer
select avg(age), min(age), max(age) from singer where country = "france"	concert_singer
select name, song_release_year from singer where age = (select min(age) from singer)	concert_singer
select song_name, song_release_year from singer where age = (select min(age) from singer)	concert_singer
select distinct country from singer where age > 20	concert_singer
select distinct country from singer where age > 20	concert_singer
select country, count(singer_id) from singer group by country	concert_singer
select country, count(singer_id) from singer group by country	concert_singer
select song_name from singer where age > (select avg(age) from singer)	concert_singer
select song_name from singer where age > (select avg(age) from singer)	concert_singer
select location, name from stadium where capacity between 5000 and 10000	concert_singer
select location, name from stadium where capacity between 5000 and 10000	concert_singer
select max(capacity), avg(capacity) from stadium	concert_singer
select avg(capacity), max(capacity) from stadium	concert_singer
select name, capacity from stadium where average = (select max(average) from stadium)	concert_singer
select name, capacity from stadium where average = (select max(average) from stadium)	concert_singer
select count(*) from concert where year = 2014 or year = 2015	concert_singer
select count(concert_id) from concert where year = 2014 or year = 2015	concert_singer
select stadium.name, count(concert.concert_id) from stadium left join concert on stadium.stadium_id = concert.stadium_id group by stadium.name	concert_singer
select stadium.name, count(concert.concert_id) from stadium left join concert on stadium.stadium_id = concert.stadium_id group by stadium.stadium_id, stadium.name	concert_singer
select s.name, s.capacity from stadium as s join concert as c on s.stadium_id = c.stadium_id where c.year > = "2014" group by s.stadium_id, s.name, s.capacity order by count(*) desc limit 1	concert_singer
select stadium.name, stadium.capacity from stadium join concert on stadium.stadium_id = concert.stadium_id where concert.year > 2013 group by stadium.stadium_id, stadium.name, stadium.capacity order by count(*) desc limit 1	concert_singer
select year from concert group by year order by count(*) desc limit 1	concert_singer
select t.year from concert as t group by t.year order by count(*) desc limit 1	concert_singer
select name from stadium where stadium_id not in (select stadium_id from concert)	concert_singer
select name from stadium s where not exists (select 1 from concert c where c.stadium_id = s.stadium_id)	concert_singer
select country from singer where age > 40 intersect select country from singer where age < 30	concert_singer
select name from stadium s where not exists (select 1 from concert c where c.stadium_id = s.stadium_id and c.year = 2014)	concert_singer
select name from stadium s where not exists (select 1 from concert c where c.stadium_id = s.stadium_id and c.year = 2014)	concert_singer
select t1.concert_name, t1.theme, count(t2.singer_id) from concert as t1 left join singer_in_concert as t2 on t1.concert_id = t2.concert_id group by t1.concert_id, t1.concert_name, t1.theme	concert_singer
select t1.concert_name, t1.theme, count(t2.singer_id) from concert as t1 left join singer_in_concert as t2 on t1.concert_id = t2.concert_id group by t1.concert_id, t1.concert_name, t1.theme	concert_singer
select singer.name, count(singer_in_concert.concert_id) from singer left join singer_in_concert on singer.singer_id = singer_in_concert.singer_id group by singer.singer_id, singer.name	concert_singer
select singer.name, count(singer_in_concert.concert_id) as num_concerts from singer left join singer_in_concert on singer.singer_id = singer_in_concert.singer_id group by singer.singer_id, singer.name	concert_singer
select singer.name from singer join singer_in_concert on singer.singer_id = singer_in_concert.singer_id join concert on singer_in_concert.concert_id = concert.concert_id where concert.year = 2014	concert_singer
select singer.name from singer join singer_in_concert on singer.singer_id = singer_in_concert.singer_id join concert on singer_in_concert.concert_id = concert.concert_id where concert.year = 2014	concert_singer
select name, country from singer where song_name like "%hey %"	concert_singer
select name, country from singer where song_name like "%hey %"	concert_singer
select t2.name, t2.location from concert as t1 join stadium as t2 on t1.stadium_id = t2.stadium_id where t1.year = 2014 intersect select t2.name, t2.location from concert as t1 join stadium as t2 on t1.stadium_id = t2.stadium_id where t1.year = 2015	concert_singer
select t2.name, t2.location from concert as t1 join stadium as t2 on t1.stadium_id = t2.stadium_id where t1.year = 2014 intersect select t2.name, t2.location from concert as t1 join stadium as t2 on t1.stadium_id = t2.stadium_id where t1.year = 2015	concert_singer
select count(*) from concert where stadium_id in (select stadium_id from stadium where capacity = (select max(capacity) from stadium))	concert_singer
select count(*) from concert where stadium_id in (select stadium_id from stadium where capacity = (select max(capacity) from stadium))	concert_singer
