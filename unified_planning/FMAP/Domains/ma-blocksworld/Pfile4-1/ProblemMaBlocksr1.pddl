(define (problem BLOCKS-4-1)
(:domain ma-blocksworld)
(:objects
 r0 r1 r2 r3 - robot
 d b a c - block
)
(:shared-data
  ((on ?b - block) - block)
  (ontable ?b - block)
  (clear ?b - block)
  ((holding ?r - robot) - block) - 
(either r0 r2 r3)
)
(:init
 (myAgent r1)
 (= (holding r0) nob)
 (= (holding r1) nob)
 (= (holding r2) nob)
 (= (holding r3) nob)
 (not (clear d))
 (ontable d)
 (= (on d) nob)
 (clear b)
 (= (on b) c)
 (not (ontable b))
 (not (clear a))
 (= (on a) d)
 (not (ontable a))
 (not (clear c))
 (= (on c) a)
 (not (ontable c))
)
(:global-goal (and
 (= (on d) c)
 (= (on c) a)
 (= (on a) b)
)))
