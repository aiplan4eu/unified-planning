
(define (problem att_log0)
  (:domain logistics_conf)
  (:objects 	package1 - OBJ
		package2 - OBJ
		package3 - OBJ
		pgh_truck - TRUCK
		bos_truck - TRUCK
		phx_truck - TRUCK
		airplane1 - AIRPLANE
		bos_po - LOCATION
		pgh_po - LOCATION
		phx_po - LOCATION
		bos_airport - AIRPORT
		pgh_airport - AIRPORT
		phx_airport - AIRPORT
		pgh - CITY
		bos - CITY
 		phx - CITY
	)
 (:init
(unknown (at_ol package1 pgh_po))
(unknown (at_ol package1 phx_po))
(unknown (at_ol package2 pgh_po))
(unknown (at_ol package2 bos_po))
(unknown (at_ol package3 bos_po))
(unknown (at_ol package3 phx_po))


	(oneof
	 (at_ol package1 pgh_po)
	 (at_ol package1 phx_po)
	 )
	(oneof
	(at_ol package2 pgh_po)
	(at_ol package2 bos_po)
	)
	(oneof
	 (at_ol package3 bos_po)
	 (at_ol package3 phx_po)
	 )

 	 (at_aa airplane1 pgh_airport)
	 (at_tl bos_truck bos_po)
	 (at_tl pgh_truck pgh_po)

	 (at_tl phx_truck phx_po)

	 (in_city_l bos_po bos)
	 (in_city_a bos_airport bos)
	 (in_city_l phx_po phx)
	 (in_city_a phx_airport phx)
	 (in_city_l pgh_po pgh)
	 (in_city_a pgh_airport pgh)
	 (in_city_t pgh_truck pgh)
	 (in_city_t bos_truck bos)
	 (in_city_t phx_truck phx)
)
(:goal
  (and
	(at_oa package1 bos_airport)
	(at_oa package2 phx_airport)
	(at_oa package3 pgh_airport)
	)
  )
)
