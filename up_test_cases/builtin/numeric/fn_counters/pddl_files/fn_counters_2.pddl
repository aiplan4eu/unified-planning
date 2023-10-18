;; Enrico Scala (enricos83@gmail.com) and Miquel Ramirez (miquel.ramirez@gmail.com)
(define (problem instance_2)
  (:domain fn-counters)
  (:objects
    c0 c1 - counter
  )

  (:init
    (= (value c0) 0)
	(= (value c1) 0)
	(= (max_int) 4)
  )

  (:goal (and 
(<= (+ (value c0) 1) (value c1))
  ))

  
  

  
)
