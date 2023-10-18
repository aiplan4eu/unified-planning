;; Enrico Scala (enricos83@gmail.com) and Miquel Ramirez (miquel.ramirez@gmail.com)
(define (problem instance_4_3)
  (:domain mt-plant-watering-constrained)
  (:objects
    tap1 - tap
	agent1 - agent
	plant3 plant1 plant4 plant2 - plant
  )

  (:init
    (= (max_int) 80)
	(= (maxx) 4)
	(= (minx) 1)
	(= (maxy) 4)
	(= (miny) 1)
	(= (carrying) 0)
	(= (total_poured) 0)
	(= (total_loaded) 0)
	(= (poured plant1) 0)
	(= (poured plant2) 0)
	(= (poured plant3) 0)
	(= (poured plant4) 0)
	(= (x agent1) 1)
	(= (y agent1) 4)
	(= (x plant2) 4)
	(= (y plant2) 4)
	(= (x plant3) 4)
	(= (y plant3) 4)
	(= (x tap1) 1)
	(= (y tap1) 1)
	(= (x plant4) 3)
	(= (y plant4) 3)
	(= (x plant1) 3)
	(= (y plant1) 3)
  )

  (:goal (and 
    (= (poured plant1) 10)
	(= (poured plant2) 5)
	(= (poured plant3) 7)
	(= (poured plant4) 4)
	(= (total_poured) (+ (+ (+ (poured plant1) (poured plant2)) (poured plant3)) (poured plant4)) )
  ))

  
  

  
)
