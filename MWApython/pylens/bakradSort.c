#include <stdio.h>
#include <limits.h>
#include <stdlib.h>
 
typedef unsigned uint;
#define swap(a, b) { tmp = a; a = b; b = tmp; }
#define swapd(a,b) { tmpd = a; a = b; b = tmpd;}
#define each(i, x) for (i = 0; i < x; i++)


static void rad_sort_u(uint *,uint *,uint);
void radsort(int *,const size_t);
void radsort2(int *,double *,const size_t,uint);
static void rad_sort_u2(uint *,uint *,double *,double *,uint);

/* sort unsigned ints */
static void rad_sort_u(uint *from, uint *to, uint bit)
{
    if (!bit || to < from + 1) return;
 
    uint *ll = from, *rr = to - 1, tmp;
    while (1) {
        /* find left most with bit, and right most without bit, swap */
        while (ll < rr && !(*ll & bit)) ll++;
        while (ll < rr &&  (*rr & bit)) rr--;
        if (ll >= rr) break;
        swap(*ll, *rr);
    }
 
    if (!(bit & *ll) && ll < to) ll++;
    bit >>= 1;
 
    rad_sort_u(from, ll, bit);
    rad_sort_u(ll, to, bit);
}

void radsort(int *a, const size_t len) {
    size_t i;
    uint *x = (uint*) a;

    each(i, len) x[i] ^= INT_MIN;
    rad_sort_u(x,x+len,INT_MIN);
    each(i, len) x[i] ^= INT_MIN;
}

void sort_csr(int *ia,int *ja, double *a, const size_t maxi, const size_t nia) {
    int i;

    uint bit = 1;
    uint mbit = INT_MIN;
    while(!(mbit & maxi)) mbit >>= 1;

    printf("%d\n",mbit);
    while(!(mbit&bit)) {
        printf("%d\n",bit);
        bit <<= 1;
    }


    each(i,nia-1) radsort2(ja+ia[i],a+ia[i],ia[i+1]-ia[i],bit);
}

void radsort2(int *a, double *d, const size_t len,uint bit) {
    size_t i;
    uint *x = (uint*) a;

    each(i, len) x[i] ^= INT_MIN;
    rad_sort_u2(x,x+len,d,d+len,bit);
    each(i, len) x[i] ^= INT_MIN;
}

static void rad_sort_u2(uint *from, uint *to, double *fromd, double *tod, uint bit)
{
    if (!bit || to < from + 1) return;

    uint *ll = from, *rr = to - 1, tmp;
    double *lld = fromd,*rrd = tod-1,tmpd;
    while (1) {
        /* find left most with bit, and right most without bit, swap */
        while (ll < rr && !(*ll & bit)) {
            ll++;
            lld++;
        }
        while (ll < rr && (*rr & bit)) {
            rr--;
            rrd--;
        }
        if (ll >= rr) break;
        swap(*ll, *rr);
        swapd(*lld,*rrd);
    }

    if (!(bit & *ll) && ll < to) {
        ll++;
        lld++;
    }
    bit >>= 1;

//    rad_sort_u2(ll,rr,lld,rrd,bit);//from,to,fromd,tod,bit);
    rad_sort_u2(from, ll, fromd, lld, bit);
    rad_sort_u2(ll, to, lld, tod, bit);
}
