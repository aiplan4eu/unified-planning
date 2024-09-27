;; edit of the original example by Enrico Scala (enricos83@gmail.com) and Miquel Ramirez (miquel.ramirez@gmail.com)
;; to make tests faster - this still verifies anytime requirements in unified_planning as of septemer 27th 2024 
;; the bloat of unused counters still makes it that the first solution is not optimal, but takes less time to run tests
(define (problem instance_12_mod)
  (:domain fn-counters)
  (:objects
    c0 c1 c2 c3 c4 c5 c6 c7 c8 c9 c10 c11 c12 c13 c14 c15 - counter
  )

  (:init
    (= (max_int) 24)
	(= (value c0) 0)
	(= (value c1) 0)
	(= (value c2) 0)
	(= (value c3) 0)
	(= (value c4) 0)
	(= (value c5) 0)
	(= (value c6) 0)
	(= (value c7) 0)
	(= (value c8) 0)
	(= (value c9) 0)
	(= (value c10) 0)
	(= (value c11) 0)
	(= (value c12) 0)
	(= (value c13) 0)
	(= (value c14) 0)
	(= (value c15) 0)
  )

  (:goal (and 
    (<= (+ (value c0) 1) (value c1))
	(<= (+ (value c1) 1) (value c2))
	(<= (+ (value c2) 1) (value c3))
	(<= (+ (value c3) 1) (value c4))
	(<= (+ (value c4) 1) (value c5))
	(<= (+ (value c5) 1) (value c6))
	(<= (+ (value c6) 1) (value c7))
  ))

  
)
