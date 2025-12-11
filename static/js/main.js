function formatPrice(value) {
  return (Math.round(value * 100) / 100).toFixed(2);
}

function loadWeekMenu() {
  const container = document.getElementById("menu-week");
  if (!container) return;

  fetch("/api/menu/week")
    .then(r => r.json())
    .then(data => {
      container.innerHTML = "";
      const today = new Date();
      const todayName = today.toLocaleDateString("en-GB", { weekday: "long" });

      if (!data.days || !data.days.length) {
        container.innerHTML = "<p>No menu found for this week yet.</p>";
        return;
      }

      data.days.forEach(day => {
        const div = document.createElement("div");
        div.className = "menu-day";
        if (day.weekday === todayName) {
          div.classList.add("today");
        }
        const title = document.createElement("h3");
        title.textContent = day.weekday + " (" + day.date + ")";
        div.appendChild(title);

        if (!day.dishes || !day.dishes.length) {
          const p = document.createElement("p");
          p.textContent = "No dishes defined.";
          div.appendChild(p);
        } else {
          day.dishes.forEach(dish => {
            const item = document.createElement("div");
            item.className = "dish";

            const info = document.createElement("div");
            info.className = "dish-info";
            info.innerHTML = "<strong>" + dish.name + "</strong><br>" +
              "<span class='dish-meta'>" + (dish.description || "") +
              (dish.diet && dish.diet.length ? " [" + dish.diet.join(", ") + "]" : "") +
              (dish.allergens && dish.allergens.length ? " Allergens: " + dish.allergens.join(", ") + "" : "") +
              "</span>";

            const controls = document.createElement("div");
            controls.innerHTML = "€" + formatPrice(dish.price || 0) +
              "<br><button class='btn btn-small' data-add-cart='1'>Add</button>";

            item.appendChild(info);
            item.appendChild(controls);

            item.dataset.dish = JSON.stringify({
              id: dish.id || (day.date + ":" + dish.name),
              name: dish.name,
              price: dish.price || 0
            });

            div.appendChild(item);
          });
        }

        container.appendChild(div);
      });

      container.addEventListener("click", (e) => {
        if (e.target.matches("button[data-add-cart]")) {
          const dishDiv = e.target.closest(".dish");
          const dishData = JSON.parse(dishDiv.dataset.dish);
          addToCart(dishData);
        }
      });
    });
}

let cart = [];

function loadCartFromStorage() {
  try {
    const stored = localStorage.getItem("cart");
    if (stored) cart = JSON.parse(stored);
  } catch (e) {
    cart = [];
  }
  renderCart();
}

function saveCart() {
  localStorage.setItem("cart", JSON.stringify(cart));
}

function addToCart(dish) {
  const existing = cart.find(i => i.id === dish.id);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({ ...dish, qty: 1 });
  }
  saveCart();
  renderCart();
}

function removeFromCart(id) {
  cart = cart.filter(i => i.id !== id);
  saveCart();
  renderCart();
}

function renderCart() {
  const container = document.getElementById("cart-items");
  const totalEl = document.getElementById("cart-total");
  if (!container || !totalEl) return;

  container.innerHTML = "";
  if (!cart.length) {
    container.innerHTML = "<p>Your cart is empty.</p>";
    totalEl.textContent = "0.00";
    return;
  }

  let total = 0;
  cart.forEach(item => {
    total += item.price * item.qty;
    const div = document.createElement("div");
    div.className = "cart-item";
    div.innerHTML = `
      <span>${item.name} x${item.qty}</span>
      <span>€${formatPrice(item.price * item.qty)} <button class="btn btn-small" data-remove="${item.id}">Remove</button></span>
    `;
    container.appendChild(div);
  });
  totalEl.textContent = formatPrice(total);

  container.addEventListener("click", (e) => {
    if (e.target.matches("button[data-remove]")) {
      const id = e.target.getAttribute("data-remove");
      removeFromCart(id);
    }
  }, { once: true });
}

function setupCheckout() {
  const btn = document.getElementById("checkout-btn");
  if (!btn) return;
  btn.addEventListener("click", () => {
    if (!cart.length) {
      alert("Cart is empty");
      return;
    }
    fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items: cart, pickupTime: null })
    }).then(r => {
      if (r && r.status === 401) {
        alert("Please log in to place an order.");
        window.location.href = "/login";
        return;
      }
      return r.json();
    }).then(data => {
      if (!data) return;
      alert("Order created! ID: " + data.id);
      cart = [];
      saveCart();
      renderCart();
    }).catch(() => {
      alert("Error creating order");
    });
  });
}

function loadTransportInfo() {
  const container = document.getElementById("transport-info");
  if (!container) return;

  fetch("/api/transport-info")
    .then(r => r.json())
    .then(data => {
      if (!data.locations || !data.locations.length) {
        container.innerHTML = "<p>No transport info available.</p>";
        return;
      }

      const list = document.createElement("ul");

      data.locations.forEach(loc => {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${loc.title}</strong> – ${loc.description}`;
        list.appendChild(li);
      });

      container.innerHTML = "";
      container.appendChild(list);
    })
    .catch(() => {
      container.innerHTML = "<p>Unable to load transport info.</p>";
    });
}

document.addEventListener("DOMContentLoaded", () => {
  loadWeekMenu();
  loadCartFromStorage();
  setupCheckout();
  loadTransportInfo();
});