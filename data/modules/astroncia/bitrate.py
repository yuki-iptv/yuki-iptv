def humanbytes(B):
   'Return the given bytes as a human friendly KB, MB, GB, or TB string'
   B = float(B)
   KB = float(1024)
   MB = float(KB ** 2) # 1,048,576
   GB = float(KB ** 3) # 1,073,741,824
   TB = float(KB ** 4) # 1,099,511,627,776

   if B < KB:
      return '{0} {1}'.format(B,'bps' if 0 == B > 1 else 'bps')
   elif KB <= B < MB:
      return '{0:.2f} kbps'.format(B/KB)
   elif MB <= B < GB:
      return '{0:.2f} Mbps'.format(B/MB)
   elif GB <= B < TB:
      return '{0:.2f} Gbps'.format(B/GB)
   elif TB <= B:
      return '{0:.2f} Tbps'.format(B/TB)
