from heapq import heapify, heappush, heappop

# An abstracted Pod class to represent Orca Pods in Python
# Only the net differences between stock and consumption of resources are needed for the purposes of this module
class Pod:
    def __init__(self, name, waterStock, foodStock, medicineStock, waterConsumption, foodConsumption, medicineConsumption):
        self.name = name  # string
        self.netWater = waterStock - waterConsumption       # int, negative = shortfall
        self.netFood = foodStock - foodConsumption          # int, negative = shortfall
        self.netMedicine = medicineStock - medicineConsumption  # int, negative = shortfall


def listPods(pods: list):
    """
    Bug fixes applied:
    - range(n) instead of range(n+1): pods is indexed 0..n-1, the old range(n+1)
      read pods[n], which is out of bounds on every non-empty call.
    - Removed reference to cur.stock: Pod never defines a `stock` attribute
      (it was commented out in __init__), only netWater/netFood/netMedicine exist.
      Printing net values directly is what the rest of the module actually uses.
    """
    n = len(pods)
    for i in range(n):
        cur: Pod = pods[i]
        print(f"Pod {cur.name} | Needs: {cur.netWater} Water, {cur.netFood} Food, {cur.netMedicine} Medicine")


def _getPriorities(pods: list, attr: str):
    """
    Shared ranking logic for a single resource. Sorts pods ascending by the
    given net-resource attribute (most negative / most urgent first), using
    a min-heap so the caller can pop-and-reinsert as allocations happen
    incrementally rather than only doing a one-shot sort.

    Bug fix: the tie-breaking counter was previously set to 1 once and never
    incremented, so it did not actually break ties. Any two non-first pods
    sharing the same net value would fall through to comparing Pod objects
    directly, which have no __lt__ defined, raising TypeError. This is
    intermittent — it only surfaces when two pods tie on the resource being
    ranked — so it can pass casual testing and fail later on real data.
    Fixed by incrementing counter on every push, giving a strict, stable,
    insertion-order tie-break.
    """
    priorityHeap = []
    heapify(priorityHeap)

    counter = 0
    for pod in pods:
        heappush(priorityHeap, (getattr(pod, attr), counter, pod))
        counter += 1

    result = []
    while priorityHeap:
        _, _, pod = heappop(priorityHeap)
        result.append(pod)

    return result


def getWaterPriorities(pods: list):
    """Pods ranked by net water, most urgent (lowest/most negative) first."""
    return _getPriorities(pods, "netWater")


def getFoodPriorities(pods: list):
    """
    Added function. The original file only ranked water; food had no
    equivalent despite Pod tracking netFood. Same tie-break-safe logic.
    """
    return _getPriorities(pods, "netFood")


def getMedicinePriorities(pods: list):
    """
    Added function. Same gap as getFoodPriorities — medicine shortfalls are
    typically the most life-critical of the three and had no ranking path.
    """
    return _getPriorities(pods, "netMedicine")


def getOverallPriorities(pods: list):
    """
    Added function. Ranks pods by their single worst resource shortfall
    (min of netWater, netFood, netMedicine), not by the sum.

    Rationale: summing the three nets would let a large surplus in one
    resource mask a critical deficit in another (e.g. plenty of water
    hiding a medicine crisis). Using the minimum ensures a pod in acute
    need on any one resource is never buried by good numbers elsewhere —
    directly relevant to the stated risk of overlooked pods like Reed's End,
    who may look fine in aggregate while being critical on one axis.

    This does not account for delivery difficulty, reporting reliability,
    or prior neglect, since Pod does not currently carry that data. Those
    would need new fields on Pod (e.g. accessibilityScore, reliabilityScore,
    cyclesSinceLastDelivery) and an explicit weighting scheme before they
    could be folded into this ranking — adding them silently here would be
    inventing data the source system doesn't provide.
    """
    priorityHeap = []
    heapify(priorityHeap)

    counter = 0
    for pod in pods:
        worst = min(pod.netWater, pod.netFood, pod.netMedicine)
        heappush(priorityHeap, (worst, counter, pod))
        counter += 1

    result = []
    while priorityHeap:
        _, _, pod = heappop(priorityHeap)
        result.append(pod)

    return result
