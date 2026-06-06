/** Primary ease for page UI — smooth deceleration */
export const easeFluid = [0.22, 1, 0.36, 1] as const;

/** Spring for cards / hero panels */
export const springSoft = { type: "spring" as const, stiffness: 200, damping: 28, mass: 0.8 };

/** Viewport: replay enter/exit when scrolling (reduced motion → play once only) */
export function scrollViewport(reduced: boolean | null) {
  if (reduced) {
    return { once: true as const, amount: 0.15 as const, margin: "0px 0px -10% 0px" as const };
  }
  return { once: false as const, amount: 0.22 as const, margin: "0px 0px -14% 0px" as const };
}

export function navTransition(reduced: boolean | null) {
  return reduced ? { duration: 0 } : { duration: 0.55, ease: easeFluid };
}

export function staggerChildren(reduced: boolean | null, stagger = 0.07) {
  return reduced ? 0 : stagger;
}
