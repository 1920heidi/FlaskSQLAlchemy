(() => {
  "use strict";

  const CATEGORY_COLORS = {
    strength: "var(--cat-strength)",
    cardio: "var(--cat-cardio)",
    flexibility: "var(--cat-flexibility)",
    balance: "var(--cat-balance)",
  };

  const MONTHS = [
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
  ];

  const state = {
    workouts: [],
    exercises: [],
    openWorkoutDetail: new Map(), // workout id -> detail payload
    openExerciseDetail: new Map(), // exercise id -> detail payload
  };

  // ------------------------------------------------------------------
  // API helpers
  // ------------------------------------------------------------------

  class ApiError extends Error {}

  async function apiRequest(url, options = {}) {
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });

    let body = null;
    const text = await res.text();
    if (text) {
      try {
        body = JSON.parse(text);
      } catch (_err) {
        body = null;
      }
    }

    if (!res.ok) {
      throw new ApiError(extractErrorMessage(body, res.status));
    }
    return body;
  }

  function extractErrorMessage(body, status) {
    if (!body) return `Request failed (${status}).`;
    if (body.error) return body.error;
    if (body.errors) {
      if (Array.isArray(body.errors)) return body.errors.join(" ");
      return Object.entries(body.errors)
        .map(([field, msgs]) => {
          const text = Array.isArray(msgs) ? msgs.join(" ") : String(msgs);
          return field === "_schema" ? text : `${field}: ${text}`;
        })
        .join(" ");
    }
    return `Request failed (${status}).`;
  }

  const api = {
    getWorkouts: () => apiRequest("/workouts"),
    getWorkout: (id) => apiRequest(`/workouts/${id}`),
    createWorkout: (data) =>
      apiRequest("/workouts", { method: "POST", body: JSON.stringify(data) }),
    deleteWorkout: (id) => apiRequest(`/workouts/${id}`, { method: "DELETE" }),

    getExercises: () => apiRequest("/exercises"),
    getExercise: (id) => apiRequest(`/exercises/${id}`),
    createExercise: (data) =>
      apiRequest("/exercises", { method: "POST", body: JSON.stringify(data) }),
    deleteExercise: (id) => apiRequest(`/exercises/${id}`, { method: "DELETE" }),

    addExerciseToWorkout: (workoutId, exerciseId, data) =>
      apiRequest(`/workouts/${workoutId}/exercises/${exerciseId}/workout_exercises`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  };

  // ------------------------------------------------------------------
  // Toasts
  // ------------------------------------------------------------------

  const toastStack = document.getElementById("toast-stack");

  function showToast(message, { error = false } = {}) {
    const toast = document.createElement("div");
    toast.className = `toast${error ? " is-error" : ""}`;
    toast.textContent = message;
    toastStack.appendChild(toast);

    setTimeout(() => {
      toast.classList.add("is-leaving");
      toast.addEventListener("animationend", () => toast.remove(), { once: true });
    }, 3200);
  }

  // ------------------------------------------------------------------
  // Tabs
  // ------------------------------------------------------------------

  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => {
        b.classList.remove("is-active");
        b.setAttribute("aria-selected", "false");
      });
      btn.classList.add("is-active");
      btn.setAttribute("aria-selected", "true");

      document.querySelectorAll(".view").forEach((v) => v.classList.remove("is-active"));
      document.getElementById(`view-${btn.dataset.tab}`).classList.add("is-active");
    });
  });

  // ------------------------------------------------------------------
  // Toggleable forms
  // ------------------------------------------------------------------

  function wireFormToggle(buttonId, formId) {
    const button = document.getElementById(buttonId);
    const form = document.getElementById(formId);
    button.addEventListener("click", () => {
      form.hidden = !form.hidden;
      if (!form.hidden) form.querySelector("input, select, textarea")?.focus();
    });
    form.querySelector("[data-cancel]").addEventListener("click", () => {
      form.reset();
      form.hidden = true;
    });
  }

  wireFormToggle("toggle-workout-form", "workout-form");
  wireFormToggle("toggle-exercise-form", "exercise-form");

  // ------------------------------------------------------------------
  // Rendering: Workouts
  // ------------------------------------------------------------------

  const workoutsListEl = document.getElementById("workouts-list");
  const workoutsEmptyEl = document.getElementById("workouts-empty");
  const workoutCountEl = document.getElementById("workout-count");
  const workoutCardTpl = document.getElementById("tpl-workout-card");
  const workoutExerciseEntryTpl = document.getElementById("tpl-workout-exercise-entry");

  function formatDate(isoDate) {
    const [year, month, day] = isoDate.split("-").map(Number);
    return { day, month: MONTHS[month - 1], year };
  }

  function renderWorkouts() {
    workoutCountEl.textContent = state.workouts.length;
    workoutsEmptyEl.hidden = state.workouts.length !== 0;
    workoutsListEl.innerHTML = "";

    state.workouts
      .slice()
      .sort((a, b) => (a.date < b.date ? 1 : -1))
      .forEach((workout, index) => {
        const node = workoutCardTpl.content.cloneNode(true);
        const card = node.querySelector(".card");
        card.style.animationDelay = `${Math.min(index * 40, 400)}ms`;
        card.dataset.id = workout.id;

        const { day, month } = formatDate(workout.date);
        node.querySelector(".date-day").textContent = day;
        node.querySelector(".date-month").textContent = month;
        node.querySelector(".duration-badge").textContent = `${workout.duration_minutes} MIN`;
        node.querySelector(".card-notes").textContent = workout.notes || "No notes.";

        workoutsListEl.appendChild(node);
        wireWorkoutCard(workoutsListEl.querySelector(`.card[data-id="${workout.id}"]`), workout);
      });
  }

  function wireWorkoutCard(cardEl, workout) {
    const header = cardEl.querySelector(".card-header");
    const detail = cardEl.querySelector(".card-detail");

    header.addEventListener("click", async () => {
      const isOpen = cardEl.classList.toggle("is-open");
      detail.hidden = !isOpen;
      if (isOpen) {
        await loadWorkoutDetail(workout.id, cardEl);
      }
    });

    cardEl.querySelector(".delete-workout").addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm("Delete this workout and everything logged in it?")) return;
      try {
        await api.deleteWorkout(workout.id);
        state.workouts = state.workouts.filter((w) => w.id !== workout.id);
        renderWorkouts();
        showToast("Workout deleted.");
      } catch (err) {
        showToast(err.message, { error: true });
      }
    });
  }

  async function loadWorkoutDetail(workoutId, cardEl) {
    const entriesEl = cardEl.querySelector(".exercise-entries");
    const emptyEl = cardEl.querySelector(".detail-empty");
    const exerciseCountBadge = cardEl.querySelector(".exercise-count-badge");
    const select = cardEl.querySelector('select[name="exercise_id"]');

    entriesEl.innerHTML = "";

    try {
      const detail = await api.getWorkout(workoutId);
      const entries = detail.workout_exercises || [];
      exerciseCountBadge.textContent = `${entries.length} exercise${entries.length === 1 ? "" : "s"}`;
      emptyEl.hidden = entries.length !== 0;

      entries.forEach((entry) => {
        const node = workoutExerciseEntryTpl.content.cloneNode(true);
        node.querySelector(".entry-category-dot").style.background =
          CATEGORY_COLORS[entry.exercise.category] || "var(--text-faint)";
        node.querySelector(".entry-name").textContent = entry.exercise.name;
        node.querySelector(".entry-metric").textContent =
          entry.duration_seconds != null
            ? `${entry.duration_seconds}s`
            : `${entry.sets}×${entry.reps}`;
        entriesEl.appendChild(node);
      });

      populateExerciseSelect(select);
    } catch (err) {
      showToast(err.message, { error: true });
    }
  }

  function populateExerciseSelect(select) {
    const current = select.value;
    select.innerHTML = '<option value="">Choose exercise&hellip;</option>';
    state.exercises
      .slice()
      .sort((a, b) => a.name.localeCompare(b.name))
      .forEach((exercise) => {
        const opt = document.createElement("option");
        opt.value = exercise.id;
        opt.textContent = exercise.name;
        select.appendChild(opt);
      });
    select.value = current;
  }

  // metric toggle + add-exercise submit — delegated once, works for every card
  workoutsListEl.addEventListener("click", (e) => {
    const metricBtn = e.target.closest(".metric-btn");
    if (!metricBtn) return;
    const form = metricBtn.closest(".add-exercise-form");
    form.querySelectorAll(".metric-btn").forEach((b) => b.classList.remove("is-active"));
    metricBtn.classList.add("is-active");
    const metric = metricBtn.dataset.metric;
    form.querySelectorAll("[data-metric-fields]").forEach((fieldset) => {
      fieldset.hidden = fieldset.dataset.metricFields !== metric;
    });
  });

  workoutsListEl.addEventListener("submit", async (e) => {
    const form = e.target.closest(".add-exercise-form");
    if (!form) return;
    e.preventDefault();

    const cardEl = form.closest(".card");
    const workoutId = cardEl.dataset.id;
    const exerciseId = form.exercise_id.value;
    if (!exerciseId) {
      showToast("Choose an exercise first.", { error: true });
      return;
    }

    const activeMetric = form.querySelector(".metric-btn.is-active").dataset.metric;
    const payload = {};
    if (activeMetric === "reps") {
      payload.sets = Number(form.sets.value) || undefined;
      payload.reps = Number(form.reps.value) || undefined;
    } else {
      payload.duration_seconds = Number(form.duration_seconds.value) || undefined;
    }

    try {
      await api.addExerciseToWorkout(workoutId, exerciseId, payload);
      form.reset();
      form.querySelectorAll(".metric-btn")[0].click();
      await loadWorkoutDetail(workoutId, cardEl);
      showToast("Exercise added to workout.");
    } catch (err) {
      showToast(err.message, { error: true });
    }
  });

  // ------------------------------------------------------------------
  // Rendering: Exercises
  // ------------------------------------------------------------------

  const exercisesListEl = document.getElementById("exercises-list");
  const exercisesEmptyEl = document.getElementById("exercises-empty");
  const exerciseCountEl = document.getElementById("exercise-count");
  const exerciseCardTpl = document.getElementById("tpl-exercise-card");

  function renderExercises() {
    exerciseCountEl.textContent = state.exercises.length;
    exercisesEmptyEl.hidden = state.exercises.length !== 0;
    exercisesListEl.innerHTML = "";

    state.exercises
      .slice()
      .sort((a, b) => a.name.localeCompare(b.name))
      .forEach((exercise, index) => {
        const node = exerciseCardTpl.content.cloneNode(true);
        const card = node.querySelector(".card");
        card.style.animationDelay = `${Math.min(index * 40, 400)}ms`;
        card.dataset.id = exercise.id;

        node.querySelector(".entry-category-dot").style.background =
          CATEGORY_COLORS[exercise.category] || "var(--text-faint)";
        node.querySelector(".exercise-name").textContent = exercise.name;
        node.querySelector(".category-label").textContent = exercise.category;
        node.querySelector(".equipment-label").textContent = exercise.equipment_needed
          ? " · Equipment required"
          : " · Bodyweight only";

        exercisesListEl.appendChild(node);
        wireExerciseCard(exercisesListEl.querySelector(`.card[data-id="${exercise.id}"]`), exercise);
      });
  }

  function wireExerciseCard(cardEl, exercise) {
    const header = cardEl.querySelector(".card-header");
    const detail = cardEl.querySelector(".card-detail");

    header.addEventListener("click", async () => {
      const isOpen = cardEl.classList.toggle("is-open");
      detail.hidden = !isOpen;
      if (isOpen) {
        await loadExerciseDetail(exercise.id, cardEl);
      }
    });

    cardEl.querySelector(".delete-exercise").addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm("Delete this exercise? It will be removed from every workout that uses it.")) return;
      try {
        await api.deleteExercise(exercise.id);
        state.exercises = state.exercises.filter((ex) => ex.id !== exercise.id);
        renderExercises();
        showToast("Exercise deleted.");
      } catch (err) {
        showToast(err.message, { error: true });
      }
    });
  }

  async function loadExerciseDetail(exerciseId, cardEl) {
    const entriesEl = cardEl.querySelector(".workout-usage-entries");
    const emptyEl = cardEl.querySelector(".detail-empty");
    entriesEl.innerHTML = "";

    try {
      const detail = await api.getExercise(exerciseId);
      const entries = detail.workout_exercises || [];
      emptyEl.hidden = entries.length !== 0;

      entries
        .slice()
        .sort((a, b) => (a.workout.date < b.workout.date ? 1 : -1))
        .forEach((entry) => {
          const li = document.createElement("li");
          li.className = "workout-usage-entry";
          const { day, month, year } = formatDate(entry.workout.date);
          const metric =
            entry.duration_seconds != null ? `${entry.duration_seconds}s` : `${entry.sets}×${entry.reps}`;
          li.innerHTML = `<span class="usage-date">${day} ${month} ${year}</span><span class="usage-metric">${metric}</span>`;
          entriesEl.appendChild(li);
        });
    } catch (err) {
      showToast(err.message, { error: true });
    }
  }

  // ------------------------------------------------------------------
  // Form submissions: create workout / exercise
  // ------------------------------------------------------------------

  document.getElementById("workout-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const payload = {
      date: form.date.value,
      duration_minutes: Number(form.duration_minutes.value),
      notes: form.notes.value || null,
    };
    try {
      const created = await api.createWorkout(payload);
      state.workouts.push(created);
      renderWorkouts();
      form.reset();
      form.hidden = true;
      showToast("Workout logged.");
    } catch (err) {
      showToast(err.message, { error: true });
    }
  });

  document.getElementById("exercise-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const payload = {
      name: form.name.value,
      category: form.category.value,
      equipment_needed: form.equipment_needed.checked,
    };
    try {
      const created = await api.createExercise(payload);
      state.exercises.push(created);
      renderExercises();
      form.reset();
      form.hidden = true;
      showToast("Exercise added to library.");
    } catch (err) {
      showToast(err.message, { error: true });
    }
  });

  // ------------------------------------------------------------------
  // Boot
  // ------------------------------------------------------------------

  async function boot() {
    try {
      const [workouts, exercises] = await Promise.all([api.getWorkouts(), api.getExercises()]);
      state.workouts = workouts;
      state.exercises = exercises;
      renderWorkouts();
      renderExercises();
    } catch (err) {
      showToast(`Could not reach the API: ${err.message}`, { error: true });
    }
  }

  boot();
})();
