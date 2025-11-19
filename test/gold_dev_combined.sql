select country from airlines where airline  =  "jetblue airways"	flight_2
select country from airlines where airline  =  "jetblue airways"	flight_2
select abbreviation from airlines where airline  =  "jetblue airways"	flight_2
select abbreviation from airlines where airline  =  "jetblue airways"	flight_2
select airline ,  abbreviation from airlines where country  =  "usa"	flight_2
select airline ,  abbreviation from airlines where country  =  "usa"	flight_2
select airportcode ,  airportname from airports where city  =  "anthony"	flight_2
select airportcode ,  airportname from airports where city  =  "anthony"	flight_2
select count(*) from airlines	flight_2
select count(*) from airlines	flight_2
select count(*) from airports	flight_2
select count(*) from airports	flight_2
select count(*) from flights	flight_2
select count(*) from flights	flight_2
select airline from airlines where abbreviation  =  "ual"	flight_2
select airline from airlines where abbreviation  =  "ual"	flight_2
select count(*) from airlines where country  =  "usa"	flight_2
select count(*) from airlines where country  =  "usa"	flight_2
select city ,  country from airports where airportname  =  "alton"	flight_2
select city ,  country from airports where airportname  =  "alton"	flight_2
select airportname from airports where airportcode  =  "ako"	flight_2
select airportname from airports where airportcode  =  "ako"	flight_2
select airportname from airports where city = "aberdeen"	flight_2
select airportname from airports where city = "aberdeen"	flight_2
select count(*) from flights where sourceairport  =  "apg"	flight_2
select count(*) from flights where sourceairport  =  "apg"	flight_2
select count(*) from flights where destairport  =  "ato"	flight_2
select count(*) from flights where destairport  =  "ato"	flight_2
select count(*) from flights as t1 join airports as t2 on t1.sourceairport  =  t2.airportcode where t2.city  =  "aberdeen"	flight_2
select count(*) from flights as t1 join airports as t2 on t1.sourceairport  =  t2.airportcode where t2.city  =  "aberdeen"	flight_2
select count(*) from flights as t1 join airports as t2 on t1.destairport  =  t2.airportcode where t2.city  =  "aberdeen"	flight_2
select count(*) from flights as t1 join airports as t2 on t1.destairport  =  t2.airportcode where t2.city  =  "aberdeen"	flight_2
select count(*) from flights as t1 join airports as t2 on t1.destairport  =  t2.airportcode join airports as t3 on t1.sourceairport  =  t3.airportcode where t2.city  =  "ashley" and t3.city  =  "aberdeen"	flight_2
select count(*) from flights as t1 join airports as t2 on t1.destairport  =  t2.airportcode join airports as t3 on t1.sourceairport  =  t3.airportcode where t2.city  =  "ashley" and t3.city  =  "aberdeen"	flight_2
select count(*) from flights as t1 join airlines as t2 on t1.airline  =  t2.uid where t2.airline = "jetblue airways"	flight_2
select count(*) from flights as t1 join airlines as t2 on t1.airline  =  t2.uid where t2.airline = "jetblue airways"	flight_2
select count(*) from airlines as t1 join flights as t2 on t2.airline  =  t1.uid where t1.airline  =  "united airlines" and t2.destairport  =  "asy"	flight_2
select count(*) from airlines as t1 join flights as t2 on t2.airline  =  t1.uid where t1.airline  =  "united airlines" and t2.destairport  =  "asy"	flight_2
select count(*) from airlines as t1 join flights as t2 on t2.airline  =  t1.uid where t1.airline  =  "united airlines" and t2.sourceairport  =  "ahd"	flight_2
select count(*) from airlines as t1 join flights as t2 on t2.airline  =  t1.uid where t1.airline  =  "united airlines" and t2.sourceairport  =  "ahd"	flight_2
select count(*) from flights as t1 join airports as t2 on t1.destairport  =  t2.airportcode join airlines as t3 on t3.uid  =  t1.airline where t2.city  =  "aberdeen" and t3.airline  =  "united airlines"	flight_2
select count(*) from flights as t1 join airports as t2 on t1.destairport  =  t2.airportcode join airlines as t3 on t3.uid  =  t1.airline where t2.city  =  "aberdeen" and t3.airline  =  "united airlines"	flight_2
select t1.city from airports as t1 join flights as t2 on t1.airportcode  =  t2.destairport group by t1.city order by count(*) desc limit 1	flight_2
select t1.city from airports as t1 join flights as t2 on t1.airportcode  =  t2.destairport group by t1.city order by count(*) desc limit 1	flight_2
select t1.city from airports as t1 join flights as t2 on t1.airportcode  =  t2.sourceairport group by t1.city order by count(*) desc limit 1	flight_2
select t1.city from airports as t1 join flights as t2 on t1.airportcode  =  t2.sourceairport group by t1.city order by count(*) desc limit 1	flight_2
select t1.airportcode from airports as t1 join flights as t2 on t1.airportcode  =  t2.destairport or t1.airportcode  =  t2.sourceairport group by t1.airportcode order by count(*) desc limit 1	flight_2
select t1.airportcode from airports as t1 join flights as t2 on t1.airportcode  =  t2.destairport or t1.airportcode  =  t2.sourceairport group by t1.airportcode order by count(*) desc limit 1	flight_2
select t1.airportcode from airports as t1 join flights as t2 on t1.airportcode  =  t2.destairport or t1.airportcode  =  t2.sourceairport group by t1.airportcode order by count(*) limit 1	flight_2
select t1.airportcode from airports as t1 join flights as t2 on t1.airportcode  =  t2.destairport or t1.airportcode  =  t2.sourceairport group by t1.airportcode order by count(*) limit 1	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline group by t1.airline order by count(*) desc limit 1	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline group by t1.airline order by count(*) desc limit 1	flight_2
select t1.abbreviation ,  t1.country from airlines as t1 join flights as t2 on t1.uid  =  t2.airline group by t1.airline order by count(*) limit 1	flight_2
select t1.abbreviation ,  t1.country from airlines as t1 join flights as t2 on t1.uid  =  t2.airline group by t1.airline order by count(*) limit 1	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline where t2.sourceairport  =  "ahd"	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline where t2.sourceairport  =  "ahd"	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline where t2.destairport  =  "ahd"	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline where t2.destairport  =  "ahd"	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline where t2.sourceairport  =  "apg" intersect select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline where t2.sourceairport  =  "cvo"	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline where t2.sourceairport  =  "apg" intersect select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline where t2.sourceairport  =  "cvo"	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline where t2.sourceairport  =  "cvo" except select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline where t2.sourceairport  =  "apg"	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline where t2.sourceairport  =  "cvo" except select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline where t2.sourceairport  =  "apg"	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline group by t1.airline having count(*)  >  10	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline group by t1.airline having count(*)  >  10	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline group by t1.airline having count(*)  <  200	flight_2
select t1.airline from airlines as t1 join flights as t2 on t1.uid  =  t2.airline group by t1.airline having count(*)  <  200	flight_2
select t1.flightno from flights as t1 join airlines as t2 on t2.uid  =  t1.airline where t2.airline  =  "united airlines"	flight_2
select t1.flightno from flights as t1 join airlines as t2 on t2.uid  =  t1.airline where t2.airline  =  "united airlines"	flight_2
select flightno from flights where sourceairport  =  "apg"	flight_2
select flightno from flights where sourceairport  =  "apg"	flight_2
select flightno from flights where destairport  =  "apg"	flight_2
select flightno from flights where destairport  =  "apg"	flight_2
select t1.flightno from flights as t1 join airports as t2 on t1.sourceairport   =  t2.airportcode where t2.city  =  "aberdeen"	flight_2
select t1.flightno from flights as t1 join airports as t2 on t1.sourceairport   =  t2.airportcode where t2.city  =  "aberdeen"	flight_2
select t1.flightno from flights as t1 join airports as t2 on t1.destairport   =  t2.airportcode where t2.city  =  "aberdeen"	flight_2
select t1.flightno from flights as t1 join airports as t2 on t1.destairport   =  t2.airportcode where t2.city  =  "aberdeen"	flight_2
select count(*) from flights as t1 join airports as t2 on t1.destairport  =  t2.airportcode where t2.city  =  "aberdeen" or t2.city  =  "abilene"	flight_2
select count(*) from flights as t1 join airports as t2 on t1.destairport  =  t2.airportcode where t2.city  =  "aberdeen" or t2.city  =  "abilene"	flight_2
select airportname from airports where airportcode not in (select sourceairport from flights union select destairport from flights)	flight_2
select airportname from airports where airportcode not in (select sourceairport from flights union select destairport from flights)	flight_2
select count(*) from singer	concert_singer
select count(*) from singer	concert_singer
select name ,  country ,  age from singer order by age desc	concert_singer
select name ,  country ,  age from singer order by age desc	concert_singer
select avg(age) ,  min(age) ,  max(age) from singer where country  =  'france'	concert_singer
select avg(age) ,  min(age) ,  max(age) from singer where country  =  'france'	concert_singer
select song_name ,  song_release_year from singer order by age limit 1	concert_singer
select song_name ,  song_release_year from singer order by age limit 1	concert_singer
select distinct country from singer where age  >  20	concert_singer
select distinct country from singer where age  >  20	concert_singer
select country ,  count(*) from singer group by country	concert_singer
select country ,  count(*) from singer group by country	concert_singer
select song_name from singer where age  >  (select avg(age) from singer)	concert_singer
select song_name from singer where age  >  (select avg(age) from singer)	concert_singer
select location ,  name from stadium where capacity between 5000 and 10000	concert_singer
select location ,  name from stadium where capacity between 5000 and 10000	concert_singer
select max(capacity), average from stadium	concert_singer
select avg(capacity) ,  max(capacity) from stadium	concert_singer
select name ,  capacity from stadium order by average desc limit 1	concert_singer
select name ,  capacity from stadium order by average desc limit 1	concert_singer
select count(*) from concert where year  =  2014 or year  =  2015	concert_singer
select count(*) from concert where year  =  2014 or year  =  2015	concert_singer
select t2.name ,  count(*) from concert as t1 join stadium as t2 on t1.stadium_id  =  t2.stadium_id group by t1.stadium_id	concert_singer
select t2.name ,  count(*) from concert as t1 join stadium as t2 on t1.stadium_id  =  t2.stadium_id group by t1.stadium_id	concert_singer
select t2.name ,  t2.capacity from concert as t1 join stadium as t2 on t1.stadium_id  =  t2.stadium_id where t1.year  >=  2014 group by t2.stadium_id order by count(*) desc limit 1	concert_singer
select t2.name ,  t2.capacity from concert as t1 join stadium as t2 on t1.stadium_id  =  t2.stadium_id where t1.year  >  2013 group by t2.stadium_id order by count(*) desc limit 1	concert_singer
select year from concert group by year order by count(*) desc limit 1	concert_singer
select year from concert group by year order by count(*) desc limit 1	concert_singer
select name from stadium where stadium_id not in (select stadium_id from concert)	concert_singer
select name from stadium where stadium_id not in (select stadium_id from concert)	concert_singer
select country from singer where age  >  40 intersect select country from singer where age  <  30	concert_singer
select name from stadium except select t2.name from concert as t1 join stadium as t2 on t1.stadium_id  =  t2.stadium_id where t1.year  =  2014	concert_singer
select name from stadium except select t2.name from concert as t1 join stadium as t2 on t1.stadium_id  =  t2.stadium_id where t1.year  =  2014	concert_singer
select t2.concert_name ,  t2.theme ,  count(*) from singer_in_concert as t1 join concert as t2 on t1.concert_id  =  t2.concert_id group by t2.concert_id	concert_singer
select t2.concert_name ,  t2.theme ,  count(*) from singer_in_concert as t1 join concert as t2 on t1.concert_id  =  t2.concert_id group by t2.concert_id	concert_singer
select t2.name ,  count(*) from singer_in_concert as t1 join singer as t2 on t1.singer_id  =  t2.singer_id group by t2.singer_id	concert_singer
select t2.name ,  count(*) from singer_in_concert as t1 join singer as t2 on t1.singer_id  =  t2.singer_id group by t2.singer_id	concert_singer
select t2.name from singer_in_concert as t1 join singer as t2 on t1.singer_id  =  t2.singer_id join concert as t3 on t1.concert_id  =  t3.concert_id where t3.year  =  2014	concert_singer
select t2.name from singer_in_concert as t1 join singer as t2 on t1.singer_id  =  t2.singer_id join concert as t3 on t1.concert_id  =  t3.concert_id where t3.year  =  2014	concert_singer
select name ,  country from singer where song_name like '%hey%'	concert_singer
select name ,  country from singer where song_name like '%hey%'	concert_singer
select t2.name ,  t2.location from concert as t1 join stadium as t2 on t1.stadium_id  =  t2.stadium_id where t1.year  =  2014 intersect select t2.name ,  t2.location from concert as t1 join stadium as t2 on t1.stadium_id  =  t2.stadium_id where t1.year  =  2015	concert_singer
select t2.name ,  t2.location from concert as t1 join stadium as t2 on t1.stadium_id  =  t2.stadium_id where t1.year  =  2014 intersect select t2.name ,  t2.location from concert as t1 join stadium as t2 on t1.stadium_id  =  t2.stadium_id where t1.year  =  2015	concert_singer
select count(*) from concert where stadium_id = (select stadium_id from stadium order by capacity desc limit 1)	concert_singer
select count(*) from concert where stadium_id = (select stadium_id from stadium order by capacity desc limit 1)	concert_singer
