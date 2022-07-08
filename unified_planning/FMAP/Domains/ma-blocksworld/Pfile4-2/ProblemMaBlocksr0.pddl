(define (problem BLOCKS-4-2)
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
(either r1 r2 r3)
)
(:init
 (myAgent r0)
 (= (holding r0) nob)
 (= (holding r1) nob)
 (= (holding r2) nob)
 (= (holding r3) nob)
 (clear d)
 (ontable d)
 (= (on d) nob)
 (not (clear b))
 (ontable b)
 (= (on b) nob)
 (clear a)
 (ontable a)
 (= (on a) nob)
 (clear c)
 (= (on c) b)
 (not (ontable c))
)
(:global-goal (and
 (= (on a) b)
 (= (on b) c)
 (= (on c) d)
)))
